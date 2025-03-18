#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import logging
import sys

from aiomqtt import Client
from email.message import EmailMessage
import aiosmtplib

import automation.config as config

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

_running = True
_task_automation = None


async def init():
    global _task_automation

    # set log level of modules logger
    for lg_name, lg_config in config.loggers.items():
        module_name = f"sail.{lg_name}"
        try:
            module = sys.modules[module_name]
        except KeyError:
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                logger.warning(f"module {module_name} not found")
                continue
        module_logger = getattr(module, "logger")
        module_logger.setLevel(lg_config.level)


async def run(config_filename: str):
    config.read(config_filename)

    await init()

    logger.info("started")
    try:
        async with Client(config.mqtt.host, config.mqtt.port) as client:
            await client.subscribe("home/doorbell/button")
            async for message in client.messages:
                if message.payload.decode() == "pressed":
                    await client.publish("home/doorbell/bell")

                    message = EmailMessage()
                    message["From"] = config.mail.fromm
                    message["To"] = config.mail.to
                    message["Subject"] = "Ding dong !"
                    message.set_content("On sonne à la porte")
                    try:
                        await aiosmtplib.send(
                            message,
                            hostname=config.smtp.host,
                            port=config.smtp.port,
                            username=config.smtp.username,
                            password=config.smtp.password
                        )
                    except Exception as exc:
                        logger.error(f"{exc}")
    except KeyboardInterrupt:
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        # loop.run_until_complete(close())
        loop.stop()
        logger.info("done")
    pass


if __name__ == "__main__":
    main()
