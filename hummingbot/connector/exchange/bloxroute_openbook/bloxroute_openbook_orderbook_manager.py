import asyncio
from typing import List, Dict

from bxsolana.provider import Provider
from bxsolana_trader_proto.api import GetOrderbookResponse, OrderbookItem

from hummingbot.connector.exchange.bloxroute_openbook.bloxroute_openbook_constants import OPENBOOK_PROJECT


class Orderbook:
    asks: List[OrderbookItem]
    bids: List[OrderbookItem]

    def __init__(self, asks: List[OrderbookItem], bids: List[OrderbookItem]):
        self.asks = asks
        self.bids = bids


class OrderbookInfo:
    best_ask_price: float = 0
    best_ask_size: float = 0
    best_bid_price: float = 0
    best_bid_size: float = 0
    latest_order_book: Orderbook

    def __init__(
        self,
        best_ask_price: float,
        best_ask_size: float,
        best_bid_price: float,
        best_bid_size: float,
        latest_order_book: Orderbook,
    ):
        self.best_ask_price = best_ask_price
        self.best_ask_size = best_ask_size
        self.best_bid_price = best_bid_price
        self.best_bid_size = best_bid_size
        self.latest_order_book = latest_order_book


class BloxrouteOpenbookOrderbookManager:
    def __init__(self, stream_provider: Provider, trading_pairs: List[str]):
        self._provider = stream_provider
        self._trading_pairs = trading_pairs
        self._order_books: Dict[str, OrderbookInfo] = {}

        self._order_book_polling_task = asyncio.create_task(self._start())

    async def _start(self):
        await self._initialize_order_books(self._trading_pairs)
        asyncio.create_task(self._poll_order_book_updates(self._trading_pairs))  # TODO do we need to stop this?

    async def _initialize_order_books(self, trading_pairs: List[str]):
        for trading_pair in trading_pairs:
            orderbook: GetOrderbookResponse = await self._provider.get_orderbook(market=trading_pair)
            self._apply_order_book_update(orderbook)

    async def _poll_order_book_updates(self, trading_pairs: List[str]):
        order_book_stream = self._provider.get_orderbooks_stream(markets=trading_pairs, project=OPENBOOK_PROJECT)
        async for order_book_update in order_book_stream:
            self._apply_order_book_update(order_book_update.orderbook)

    def _apply_order_book_update(self, update: GetOrderbookResponse):
        best_ask = update.asks[-1]
        best_bid = update.bids[0]

        self._order_books[update.market] = OrderbookInfo(
            best_ask_price=best_ask.price,
            best_ask_size=best_ask.size,
            best_bid_price=best_bid.price,
            best_bid_size=best_bid.size,
            latest_order_book=Orderbook(update.asks, update.bids),
        )

    def get_order_book(self, trading_pair: str) -> Orderbook:
        return self._order_books[trading_pair].latest_order_book

    def get_price_with_opportunity_size(self, trading_pair: str, is_bid: bool) -> (float, float):
        ob_info = self._order_books[trading_pair]
        return (
            (ob_info.best_bid_price, ob_info.best_bid_size)
            if is_bid
            else (ob_info.best_ask_price, ob_info.best_ask_size)
        )
