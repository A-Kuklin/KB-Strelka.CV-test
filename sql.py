import asyncio
import logging

import asyncpg

from config import (POSTGRESQL_HOST, POSTGRESQL_NAME, POSTGRESQL_PASSWORD,
                    POSTGRESQL_USERNAME)

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s '
                           u'[%(asctime)s]  %(message)s',
                    level=logging.INFO)


async def create_db():
    create_db_command = open("create_db.sql", "r").read()

    logging.info("Connecting to database...")
    conn: asyncpg.Connection = await asyncpg.connect(
        user=POSTGRESQL_USERNAME,
        password=POSTGRESQL_PASSWORD,
        database=POSTGRESQL_NAME,
        host=POSTGRESQL_HOST
    )
    await conn.execute(create_db_command)
    await conn.close()
    logging.info("Tables created")


async def create_pool():
    return await asyncpg.create_pool(
        user=POSTGRESQL_USERNAME,
        password=POSTGRESQL_PASSWORD,
        database=POSTGRESQL_NAME,
        host=POSTGRESQL_HOST
    )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_db())
