import asyncio
import logging

import aiosqlite
from sqlite3 import Error as Sqlite3Error

import automations.config as config

_conn = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def create_tables():
    await _conn.execute(
        "CREATE TABLE IF NOT EXISTS linky ("
        "    east INTEGER,"
        "    sinst INTEGER,"
        "    timestamp TIMESTAMP(1) DEFAULT (STRFTIME('%s', 'NOW'))"
        ");"
    )

    await _conn.execute(
        "CREATE TABLE IF NOT EXISTS linky_snapshot ("
        "    east INTEGER,"
        "    timestamp TIMESTAMP(1) DEFAULT (STRFTIME('%s', 'NOW'))"
        ");"
    )

    await _conn.execute(
        "CREATE TABLE IF NOT EXISTS on_off ("
        "    device VARCHAR(30),"
        "    state boolean,"
        "    timestamp TIMESTAMP(1) DEFAULT (STRFTIME('%s', 'NOW'))"
        ");"
    )

    await _conn.execute(
        "CREATE TABLE IF NOT EXISTS pressure ("
        "    pressure REAL,"
        "    timestamp TIMESTAMP(1) DEFAULT (STRFTIME('%s', 'NOW'))"
        ");"
    )

    await _conn.execute(
        "CREATE TABLE IF NOT EXISTS temperature_humidity ("
        "    device VARCHAR(30),"
        "    humidity REAL,"
        "    temperature REAL,"
        "    timestamp TIMESTAMP(1) DEFAULT (STRFTIME('%s', 'NOW'))"
        ");"
    )


async def init():
    global _conn

    try:
        _conn = await aiosqlite.connect(config.database.path, autocommit=True)
        await create_tables()
    except Sqlite3Error as exc:
        logger.error(f"error while creating tables ({exc})")


async def execute_query(query: str, *args):
    if _conn is not None:
        try:
            await _conn.execute(query, args)
        except Sqlite3Error as exc:
            logger.error(f"error while executing query ({exc})")


async def close():
    global _conn

    if _conn is not None:
        await _conn.close()
        _conn = None


async def run(config_filename: str):
    config.read(config_filename)

    await init()

    try:
        await execute_query(
            "INSERT INTO on_off(device, state) VALUES (?, ?)", "doorbell", True
        )

        await execute_query(
            "INSERT INTO linky(east, sinst) VALUES (?, ?)", 1000, 2000
        )

        await execute_query(
            "INSERT INTO pressure(pressure) VALUES (?)", 1013.25
        )

        await execute_query(
            "INSERT INTO temperature_humidity(device, humidity, temperature) VALUES (?, ?, ?)",
            "sejour", 50.0, 21.0
        )
    finally:
        await close()


if __name__ == "__main__":
    import argparse
    import sys

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        loop.run_until_complete(close())
        loop.stop()
    finally:
        print("done")
