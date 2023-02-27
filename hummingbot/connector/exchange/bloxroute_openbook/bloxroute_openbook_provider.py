import asyncio

import bxsolana


class BloxrouteOpenbookProviderManager(bxsolana.provider.WsProvider):
    _provider_connected = asyncio.Event()

    def __init__(self, endpoint: str, auth_header: str, private_key: str):
        super().__init__(endpoint=endpoint, auth_header=auth_header, private_key=private_key)
        asyncio.create_task(self._connect())

    async def _connect(self):
        await self.connect()
        self._provider_connected.set()

    async def wait_connect(self):
        await self._provider_connected.wait()
    @property
    def connected(self):
        return self._provider_connected.is_set()
