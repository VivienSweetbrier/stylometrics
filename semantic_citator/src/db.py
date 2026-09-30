import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool

POSTGRES_URI = os.getenv(
    "DATABASE_URL", 
    "postgres://postgres:postgres@localhost:5432/semantic_citator"
)

@asynccontextmanager
async def get_postgres_pool():
    async with AsyncConnectionPool(
        conninfo=POSTGRES_URI,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": 0}
    ) as pool:
        yield pool
