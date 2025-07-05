import argparse
import asyncio
import logging

import aiohttp

import automations.config as config
import automations.db as db

# # logger initial setup
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)


async def run(config_filename: str):
    config.read(config_filename)

    await db.init()

    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{config.domio.hostname}:{config.domio.port}/linky"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = (await resp.json())["data"]

                    # store values in db
                    await db.execute_query(
                        "INSERT INTO linky_snapshot VALUES (?)", data["east"]
                    )
    finally:
        await db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    asyncio.run(run(args.config))
