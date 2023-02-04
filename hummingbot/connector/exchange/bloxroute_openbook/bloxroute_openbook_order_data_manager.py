import asyncio
import time
from asyncio import Task
from typing import Dict, List, Optional

from bxsolana.provider import Provider
from bxsolana_trader_proto.api import GetOrderbookResponse, GetOrderStatusResponse, OrderbookItem, OrderStatus, Side

from hummingbot.client.hummingbot_application import HummingbotApplication
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
        timestamp: float
    ):
        self.best_ask_price = best_ask_price
        self.best_ask_size = best_ask_size
        self.best_bid_price = best_bid_price
        self.best_bid_size = best_bid_size
        self.latest_order_book = latest_order_book
        self.timestamp = timestamp


class OrderStatusInfo:
    order_status: OrderStatus
    quantity_released: float
    quantity_remaining: float
    side: Side
    fill_price: float
    order_price: float
    client_order_i_d: int
    timestamp: float

    def __init__(
        self,
        order_status: OrderStatus,
        quantity_released: float,
        quantity_remaining: float,
        side: Side,
        fill_price: float,
        order_price: float,
        client_order_i_d: int,
        timestamp: float,
    ):
        self.order_status = order_status
        self.quantity_released = quantity_released
        self.quantity_remaining = quantity_remaining
        self.side = side
        self.fill_price = fill_price
        self.order_price = order_price
        self.client_order_i_d = client_order_i_d
        self.timestamp = timestamp

    def __eq__(self, other: "OrderStatusInfo"):
        return (
            self.order_status == other.order_status
            and self.quantity_released == other.quantity_released
            and self.quantity_remaining == other.quantity_remaining
            and self.side == other.side
            and self.fill_price == other.fill_price
            and self.order_price == other.order_price
            and self.client_order_i_d == other.client_order_i_d
            and self.timestamp == other.timestamp
        )


class BloxrouteOpenbookOrderDataManager:
    def __init__(self, provider: Provider, trading_pairs: List[str], owner_address: str, start_timeout: int = 10):
        self._provider = provider
        self._owner_address = owner_address
        self._start_timeout = start_timeout

        for index, trading_pair in enumerate(trading_pairs):
            trading_pairs[index] = normalize_trading_pair(trading_pair)
        self._trading_pairs = trading_pairs

        self._order_books: Dict[str, OrderbookInfo] = {}
        self._markets_to_order_statuses: Dict[str, Dict[int, List[OrderStatusInfo]]] = {}

        self._started = False
        self._ready = asyncio.Event()
        self._is_ready = False

        self._orderbook_polling_task: Optional[Task] = None
        self._order_status_running_tasks: List[Task] = []
        self._order_status_polling_task: Optional[Task] = None

    async def ready(self):
        await self._ready.wait()

    @property
    def is_ready(self):
        return self._is_ready

    @property
    def started(self):
        return self._started

    async def start(self):
        if not self._started:
            self._started = True
            await self._initialize_order_books()
            self._orderbook_polling_task = asyncio.create_task(self._poll_order_book_updates())

            await self._initialize_order_status_streams()

            await asyncio.sleep(self._start_timeout)

            self._is_ready = True
            self._ready.set()

    async def stop(self):
        await self._provider.close()
        if self._orderbook_polling_task is not None:
            self._orderbook_polling_task.cancel()
            self._orderbook_polling_task = None
        for task in self._order_status_running_tasks:
            if task is not None:
                task.cancel()
        self._order_status_running_tasks.clear()

    async def _initialize_order_books(self):
        await self._provider.connect()
        for trading_pair in self._trading_pairs:
            initialized = False
            for i in range(5):
                blxr_orderbook = await self._provider.get_orderbook(market=trading_pair, limit=5, project=OPENBOOK_PROJECT)
                if blxr_orderbook.market != "":
                    self._apply_order_book_update(blxr_orderbook)
                    initialized = True

                    break
            if not initialized:
                raise Exception(f"orderbook for {trading_pair} not initialized")

    async def _initialize_order_status_streams(self):
        for trading_pair in self._trading_pairs:
            self._markets_to_order_statuses.update({trading_pair: {}})

            initialize_order_stream_task = asyncio.create_task(
                self._poll_order_status_updates(trading_pair=trading_pair)
            )
            self._order_status_running_tasks.append(initialize_order_stream_task)

    async def _poll_order_book_updates(self):
        await self._provider.connect()
        order_book_stream = self._provider.get_orderbooks_stream(
            markets=self._trading_pairs, limit=5, project=OPENBOOK_PROJECT
        )

        async for order_book_update in order_book_stream:
            self._apply_order_book_update(order_book_update.orderbook)

    async def _poll_order_status_updates(self, trading_pair: str):
        await self._provider.connect()
        order_status_stream = self._provider.get_order_status_stream(
            market=trading_pair, owner_address=self._owner_address, project=OPENBOOK_PROJECT
        )

        while True:
            order_status_update = await order_status_stream.__anext__()
            self._apply_order_status_update(order_status_update.order_info)

    def _apply_order_book_update(self, update: GetOrderbookResponse):
        normalized_trading_pair = normalize_trading_pair(update.market)

        best_ask = update.asks[0] if update.asks else OrderbookItem(price=0, size=0)
        best_bid = update.bids[-1] if update.bids else OrderbookItem(price=0, size=0)

        best_ask_price = best_ask.price
        best_ask_size = best_ask.size
        best_bid_price = best_bid.price
        best_bid_size = best_bid.size

        latest_order_book = Orderbook(update.asks, update.bids)

        self._order_books.update(
            {
                normalized_trading_pair: OrderbookInfo(
                    best_ask_price=best_ask_price,
                    best_ask_size=best_ask_size,
                    best_bid_price=best_bid_price,
                    best_bid_size=best_bid_size,
                    latest_order_book=latest_order_book,
                    timestamp=time.time()
                )
            }
        )

    def _apply_order_status_update(self, os_update: GetOrderStatusResponse):
        normalized_trading_pair = normalize_trading_pair(os_update.market)
        if normalized_trading_pair not in self._markets_to_order_statuses:
            raise Exception(f"order manager does not support updates for ${normalized_trading_pair}")

        order_statuses = self._markets_to_order_statuses[normalized_trading_pair]
        client_order_id = os_update.client_order_i_d
        order_status_info = OrderStatusInfo(
            order_status=os_update.order_status,
            quantity_released=os_update.quantity_released,
            quantity_remaining=os_update.quantity_remaining,
            side=os_update.side,
            fill_price=os_update.fill_price,
            order_price=os_update.order_price,
            client_order_i_d=client_order_id,
            timestamp=time.time(),
        )

        updated = False
        if client_order_id in order_statuses:
            if order_statuses[client_order_id][-1].order_status != os_update.order_status or order_statuses[client_order_id][-1].quantity_remaining != os_update.quantity_remaining:
                order_statuses[client_order_id].append(order_status_info)
                updated = True
        else:
            order_statuses[client_order_id] = [order_status_info]
            updated = True

        if updated:
            remaining = order_status_info.quantity_remaining
            released = order_status_info.quantity_released
            if order_status_info.side == Side.S_BID:
                remaining = remaining / order_status_info.order_price
                released = released / order_status_info.order_price
            HummingbotApplication.main_application().notify(f"order type {order_status_info.order_status.name} | quantity released: {released} | "
                                                            f"quantity remaining: {remaining} | price:  {order_status_info.order_price} | "
                                                            f"side: {order_status_info.side.name} | id {client_order_id}")

    def get_order_book(self, trading_pair: str) -> (Orderbook, float):
        normalized_trading_pair = normalize_trading_pair(trading_pair)
        if normalized_trading_pair not in self._order_books:
            raise Exception(f"order book manager does not support ${trading_pair}")

        ob_info = self._order_books[normalized_trading_pair]
        return ob_info.latest_order_book, ob_info.timestamp

    def get_price_with_opportunity_size(self, trading_pair: str, is_buy: bool) -> (float, float):
        normalized_trading_pair = normalize_trading_pair(trading_pair)
        if normalized_trading_pair not in self._order_books:
            raise Exception(f"order book manager does not support ${trading_pair}")

        ob_info = self._order_books[normalized_trading_pair]
        return (
            (ob_info.best_bid_price, ob_info.best_bid_size)
            if is_buy
            else (ob_info.best_ask_price, ob_info.best_ask_size)
        )

    def get_order_status(self, trading_pair: str, client_order_id: int) -> List[OrderStatusInfo]:
        normalized_trading_pair = normalize_trading_pair(trading_pair)
        if normalized_trading_pair not in self._markets_to_order_statuses:
            raise Exception(f"order book manager does not support ${trading_pair}")

        order_statuses = self._markets_to_order_statuses[normalized_trading_pair]
        if client_order_id in order_statuses:
            return order_statuses[client_order_id]

        return []


def normalize_trading_pair(trading_pair: str):
    trading_pair = trading_pair.replace("-", "")
    trading_pair = trading_pair.replace("/", "")
    return trading_pair
