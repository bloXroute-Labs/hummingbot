import asyncio
from collections.abc import AsyncGenerator
from time import time
from typing import List, Tuple
from unittest.mock import AsyncMock, patch

import aiounittest
import bxsolana.provider.grpc
from bxsolana.provider.constants import TESTNET_API_GRPC_HOST, TESTNET_API_GRPC_PORT
from bxsolana_trader_proto import GetOrderbookResponse, GetOrderbooksStreamResponse, OrderbookItem

from hummingbot.connector.exchange.bloxroute_openbook.bloxroute_openbook_constants import OPENBOOK_PROJECT
from hummingbot.connector.exchange.bloxroute_openbook.bloxroute_openbook_orderbook_manager import (
    BloxrouteOpenbookOrderbookManager,
)


class TestOrderbookManager(aiounittest.AsyncTestCase):
    @patch('bxsolana.provider.GrpcProvider.get_orderbook')
    async def test_initalize_orderbook(self, mock: AsyncMock):
        provider = bxsolana.provider.GrpcProvider()

        bids = orders([(5, 2), (6, 7)])
        asks = orders([(3, 4), (4, 4)])
        mock.return_value = GetOrderbookResponse(
            market="SOLUSDC",
            market_address="SOL_USDC_Market",
            bids=bids,
            asks=asks,
        )

        ob_manager = BloxrouteOpenbookOrderbookManager(provider, ["SOLUSDC"])
        await ob_manager.ready()

        ob = ob_manager.get_order_book("SOLUSDC")
        self.assertListEqual(bids, ob.bids)
        self.assertListEqual(asks, ob.asks)

        self.assertEqual((5, 2), ob_manager.get_price_with_opportunity_size("SOLUSDC", True))
        self.assertEqual((4, 4), ob_manager.get_price_with_opportunity_size("SOLUSDC", False))

        await ob_manager.stop()

    @patch('bxsolana.provider.GrpcProvider.get_orderbooks_stream')
    @patch('bxsolana.provider.GrpcProvider.get_orderbook')
    async def test_apply_update(self, orderbook_mock: AsyncMock, orderbook_stream_mock: AsyncMock):
        provider = bxsolana.provider.GrpcProvider()

        # same as first test
        bids = orders([(5, 2), (6, 7)])
        asks = orders([(3, 4), (4, 4)])
        orderbook_mock.return_value = GetOrderbookResponse(
            market="SOLUSDC",
            market_address="SOL_USDC_Market",
            bids=bids,
            asks=asks,
        )

        # new values
        new_bids = orders([(10, 2), (12, 7)])
        new_asks = orders([(2, 3), (3, 4)])
        orderbook_stream_mock.return_value = async_generator("SOLUSDC", new_bids, new_asks)

        ob_manager = BloxrouteOpenbookOrderbookManager(provider, ["SOLUSDC"])
        await ob_manager.ready()
        await asyncio.sleep(0.1)

        ob = ob_manager.get_order_book("SOLUSDC")
        self.assertListEqual(new_bids, ob.bids)
        self.assertListEqual(new_asks, ob.asks)

        self.assertEqual((10, 2), ob_manager.get_price_with_opportunity_size("SOLUSDC", True))
        self.assertEqual((3, 4), ob_manager.get_price_with_opportunity_size("SOLUSDC", False))

        await ob_manager.stop()

    async def test_run_get_server_time(self):
        provider = bxsolana.provider.WsProvider(
            auth_header="YmUwMjRkZjYtNGJmMy00MDY0LWE4MzAtNjU4MGM3ODhkM2E4OmY1ZWVhZTgxZjcwMzE5NjQ0ZmM3ZDYwNmIxZjg1YTUz",
            private_key="3mvTYCLXLM3e2oucFQCtGbtR4bHkEDAJcSkq45mRVNuP7xtpvS5nGMBsHZYVRNHGqiktoBEBBdcvgGASU1DTodPM")

        before = time()
        await provider.connect()
        # raise Exception(f"yeet {time() - before}")
        st = await provider.get_server_time()
        after = time()
        ob = await provider.get_orderbook(market="SOLUSDC", project=OPENBOOK_PROJECT)
        raise Exception(f"yeet {after - before}")

def orders(price_and_sizes: List[Tuple[int, int]]) -> List[OrderbookItem]:
    orderbook_items = []
    for price, size in price_and_sizes:
        orderbook_items.append(OrderbookItem(price=price, size=size))

    return orderbook_items


async def async_generator(market, bids, asks) -> AsyncGenerator:
    yield GetOrderbooksStreamResponse(
        slot=1,
        orderbook=GetOrderbookResponse(
            market=market,
            bids=bids,
            asks=asks
        )
    )
