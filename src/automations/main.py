import argparse
import asyncio
import logging
import signal
import sys

import automations.config as config
import automations.db as db
import automations.tasks as tasks
from automations.logger import close as logger_close
from automations.logger import init as logger_init

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def init():
    logger_init(config.loggers)
    await db.init()
    tasks.init()


async def run(config_filename: str):
    config.read(config_filename)

    await init()
    logger_close()

    while True:
        await asyncio.sleep(60)


async def close():
    await tasks.close()
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
