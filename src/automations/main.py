import argparse
import asyncio
import importlib
import logging
import signal
import sys

import automations.config as config
import automations.db as db
import automations.automations as automations

__version__ = "1.0.0"

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def _set_loggers_level(config_loggers: dict, module_path: list):
    # set log level of modules logger
    for lg_name, lg_config in config_loggers.items():
        if isinstance(lg_config, dict):
            module_path.append(lg_name)
            _set_loggers_level(lg_config, module_path)
        elif isinstance(lg_config, str):
            this_module_path = '.'.join(module_path + [lg_name])
            try:
                importlib.import_module(this_module_path)
            except ModuleNotFoundError:
                logger.warning(f"module {this_module_path} not found")
                continue

            level = getattr(logging, lg_config)
            if lg_name in logging.Logger.manager.loggerDict.keys():
                logging.getLogger(lg_name).setLevel(level)
        else:
            raise Exception("incorrect type")


async def init():
    _set_loggers_level(config.loggers, [])

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


def main():
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
