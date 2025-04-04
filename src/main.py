#!/usr/bin/env python3

import asyncio
import importlib
import logging
import sys

import aiohttp
from aiomqtt import Client
import aiosmtplib
from email.message import EmailMessage

import config

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


async def init():
    # set log level of modules logger
    for lg_name, lg_config in config.loggers.items():
        module_name = f"src.{lg_name}"
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


async def _task_doorbell():
    logger.info("started")
    try:
        async with Client(config.mqtt.hostname, config.mqtt.port) as client:
            await client.subscribe("home/doorbell/button")
            async for message in client.messages:
                if message.payload.decode() == "pressed":
                    await client.publish("home/doorbell/bell")

                    message = EmailMessage()
                    message["From"] = config.secrets.mail_from,
                    message["To"] = config.secrets.mail_to
                    message["Subject"] = "Ding dong !"
                    message.set_content("On sonne à la porte")
                    try:
                        await aiosmtplib.send(
                            message,
                            hostname=config.smtp.host,
                            port=config.smtp.port,
                            username=config.secrets.smtp_username,
                            password=config.secrets.smtp_password
                        )
                    except Exception as exc:
                        logger.error(f"{exc}")
    except KeyboardInterrupt:
        return


async def _task_pressure():
    while True:
        async with aiohttp.ClientSession() as session:
            url = f"http://{config.domotik.hostname}:{config.domotik.port}/pressure"
            async with session.get(url) as resp:
                if resp.status == 200:
                    json = await resp.json()
                    pressure = json["data"]["pressure"]
                    logger.debug(f"pressure: {pressure}")
                else:
                    logger.debug(f"bad status ({resp.status}) when getting pressure")

        await asyncio.sleep(60)


async def run(config_filename: str, secrets):
    config.read(config_filename)

    await init()

    asyncio.create_task(_task_doorbell())
    asyncio.create_task(_task_pressure())


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run(args.configs))
    except KeyboardInterrupt:
        pass
    finally:
        # loop.run_until_complete(close())
        loop.stop()
        logger.info("done")


if __name__ == "__main__":
    main()
