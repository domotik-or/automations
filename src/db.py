import asyncio
import logging

import config
import asyncpg

_db_pool = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def init():
    global _db_pool

    if _db_pool is None:
        dsn = (
            f"postgres://{config.postgresql.username}:{config.secret_data.pgpassword}"
            f"@{config.postgresql.hostname}:{config.postgresql.port}/{config.postgresql.databasename}"
        )
        _db_pool = await asyncpg.create_pool(dsn=dsn)


async def execute_query(query: str, *args):
    if _db_pool is not None:
        async with _db_pool.acquire() as conn:  # type: ignore[union-attr]
            await conn.execute(query, *args)


async def close_db():
    global _db_pool

    if _db_pool is not None:
        _db_pool.close()
        _db_pool = None


async def run(config_filename: str):
    config.read(config_filename)

    await init()

    await execute_query(
        "INSERT INTO on_off VALUES ($1, $2)", "doorbell", True
    )

    await execute_query(
        "INSERT INTO linky VALUES ($1, $2)", 1000, 2000
    )

    await execute_query(
        "INSERT INTO pressure VALUES ($1)", 1013.25
    )

    await execute_query(
        "INSERT INTO sonoff_snzb02p VALUES ($1, $2, $3)",
        "sejour", 50.0, 21.0
    )


async def close():
    await close_db()


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
