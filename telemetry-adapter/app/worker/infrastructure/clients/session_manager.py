from contextlib import AsyncExitStack

from aiobotocore.session import AioSession


class AWSSessionManager:
    def __init__(self, resource_name, **kwargs):
        self._exit_stack = AsyncExitStack()
        self._client = None
        self._resource_name = resource_name
        self._create_client_kwargs = kwargs

    async def __aenter__(self):
        session = AioSession()
        client = session.create_client(self._resource_name, **self._create_client_kwargs)
        self._client = await self._exit_stack.enter_async_context(client)
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
