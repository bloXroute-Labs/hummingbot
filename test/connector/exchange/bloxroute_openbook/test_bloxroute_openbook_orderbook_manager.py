import asyncio
import unittest
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiounittest
import bxsolana.provider.grpc
import pytest
from bxsolana_trader_proto import GetOrderbookResponse, GetOrderbooksStreamResponse, OrderbookItem

from hummingbot.connector.exchange.bloxroute_openbook.bloxroute_openbook_orderbook_manager import (
    BloxrouteOpenbookOrderbookManager,
    Orderbook,
)

# initalize orderbook
# apply update

# get orderbook
# get best price

class TestOrderbookManager(aiounittest.AsyncTestCase):
    @patch('bxsolana.provider.GrpcProvider.get_orderbook')
    async def test_initalize_orderbook(self, mock: AsyncMock):
        provider = bxsolana.provider.GrpcProvider()

        bids = [OrderbookItem(price=5, size=2), OrderbookItem(price=6, size=7)]
        asks = [OrderbookItem(price=2, size=3), OrderbookItem(price=3, size=4)]
        mock.return_value = GetOrderbookResponse(
            market="SOLUSDC",
            market_address="SOL_USDC_Market",
            bids=bids,
            asks=asks,
        )

        ob_manager = BloxrouteOpenbookOrderbookManager(provider, ["SOLUSDC"])
        await asyncio.sleep(0.1)

        self.assertEqual(ob_manager.ready, True)

        ob = ob_manager.get_order_book("SOLUSDC")
        self.assertListEqual(bids, ob.bids)
        self.assertListEqual(asks, ob.asks)

        self.assertEqual((5, 2), ob_manager.get_price_with_opportunity_size("SOLUSDC", True))
        self.assertEqual((3, 4), ob_manager.get_price_with_opportunity_size("SOLUSDC", False))

        await ob_manager.stop()

    @patch('bxsolana.provider.GrpcProvider.get_orderbooks_stream')
    @patch('bxsolana.provider.GrpcProvider.get_orderbook')
    async def test_apply_update(self, orderbook_mock: AsyncMock, orderbook_stream_mock: AsyncMock):
        provider = bxsolana.provider.GrpcProvider()

        bids = [OrderbookItem(price=5, size=2), OrderbookItem(price=6, size=7)]
        asks = [OrderbookItem(price=3, size=3), OrderbookItem(price=4, size=4)]
        orderbook_mock.return_value = GetOrderbookResponse(
            market="SOLUSDC",
            market_address="SOL_USDC_Market",
            bids=bids,
            asks=asks,
        )

        new_bids = [OrderbookItem(price=10, size=2), OrderbookItem(price=12, size=7)]
        new_asks = [OrderbookItem(price=2, size=3), OrderbookItem(price=3, size=4)]

        orderbook_stream_mock.return_value = async_generator("SOLUSDC", new_bids, new_asks)

        ob_manager = BloxrouteOpenbookOrderbookManager(provider, ["SOLUSDC"])
        await asyncio.sleep(0.1)

        self.assertEqual(ob_manager.ready, True)

        ob = ob_manager.get_order_book("SOLUSDC")
        self.assertListEqual(new_bids, ob.bids)
        self.assertListEqual(new_asks, ob.asks)

        self.assertEqual((10, 2), ob_manager.get_price_with_opportunity_size("SOLUSDC", True))
        self.assertEqual((3, 4), ob_manager.get_price_with_opportunity_size("SOLUSDC", False))

        await ob_manager.stop()


async def async_generator(market, bids, asks) -> AsyncGenerator:
    yield GetOrderbooksStreamResponse(
        slot=1,
        orderbook=GetOrderbookResponse(
            market=market,
            bids=bids,
            asks=asks
        )
    )
