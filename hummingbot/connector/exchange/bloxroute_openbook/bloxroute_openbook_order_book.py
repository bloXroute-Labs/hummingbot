from dataclasses import dataclass
from typing import Dict, List, Optional

from bxsolana_trader_proto import GetOrderbookResponse, api
from bxsolana_trader_proto.api import OrderbookItem

from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_book_row import OrderBookRow


@dataclass
class Orderbook:
    asks: List[api.OrderbookItem]
    bids: List[api.OrderbookItem]


@dataclass
class OrderbookInfo:
    best_ask_price: float
    best_ask_size: float
    best_bid_price: float
    best_bid_size: float
    latest_order_book: Orderbook
    timestamp: float


@dataclass
class OrderStatusInfo:
    order_status: api.OrderStatus
    quantity_released: float
    quantity_remaining: float
    side: api.Side
    fill_price: float
    order_price: float
    client_order_i_d: int
    timestamp: float

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


class BloxrouteOpenbookOrderBook(OrderBook):
    def apply_orderbook_snapshot(
        self, msg: Dict[str, any], timestamp: float, metadata: Optional[Dict] = None
    ):
        if msg["orderbook"]:
            if metadata:
                msg.update(metadata)
            orderbook: GetOrderbookResponse = msg["orderbook"]
            self.apply_snapshot(
                asks=orders_to_orderbook_rows(orderbook.asks),
                bids=orders_to_orderbook_rows(orderbook.bids),
                update_id=int(timestamp),
            )
        else:
            raise Exception(f"orderbook snapshot update did not contain `orderbook` field: {msg}")


def orders_to_orderbook_rows(orders: List[OrderbookItem]) -> List[OrderBookRow]:
    orderbook_rows = []
    for order in orders:
        orderbook_rows.append(order_to_orderbook_row(order))

    return orderbook_rows


def order_to_orderbook_row(order: OrderbookItem) -> OrderBookRow:
    return OrderBookRow(price=order.price, amount=order.size, update_id=order.order_i_d)
