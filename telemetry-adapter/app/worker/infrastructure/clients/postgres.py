from contextlib import AsyncExitStack

from psycopg_pool import AsyncConnectionPool


class PostgresClient:
    def __init__(self, url):
        self.url = url


class PostgresPoolManager:
    def __init__(self, db_url: str, min_pool_size: int, max_pool_size: int = None):
        self._exit_stack = AsyncExitStack()
        self._db_url = db_url
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._pool = None

    async def __aenter__(self):
        pool = AsyncConnectionPool(conninfo=self._db_url)
        self._pool = await self._exit_stack.enter_async_context(pool)
        return self._pool

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
