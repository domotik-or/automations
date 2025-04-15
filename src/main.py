#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import logging
import signal
import sys

import config
import db
import automations

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


async def init():
    # set log level of modules logger
    for lg_name, lg_config in config.loggers.items():
        try:
            importlib.import_module(lg_name)
        except ModuleNotFoundError:
            logger.warning(f"module {lg_name} not found")
            continue

        if lg_name in logging.Logger.manager.loggerDict.keys():
            logging.getLogger(lg_name).setLevel(lg_config.level)

    await db.init()
    automations.init()


async def run(config_filename: str):
    config.read(config_filename)

    await init()

    while True:
        await asyncio.sleep(60)


async def close():
    await automations.close()
    await db.close()


def sigterm_handler(_signo, _stack_frame):
    # raises SystemExit(0):
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigterm_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(close())
        loop.stop()
        logger.info("done")
