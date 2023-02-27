import asyncio

import bxsolana


class BloxrouteOpenbookProvider(bxsolana.provider.WsProvider):
    _provider_connected = asyncio.Event()

    def __init__(self, endpoint: str, auth_header: str, private_key: str):
        super().__init__(endpoint=endpoint, auth_header=auth_header, private_key=private_key)

    async def connect(self):
        await super().connect()
        self._provider_connected.set()

    async def wait_connect(self):
        await self._provider_connected.wait()
        print("done waiting")

    @property
    def connected(self):
        return self._provider_connected.is_set()
