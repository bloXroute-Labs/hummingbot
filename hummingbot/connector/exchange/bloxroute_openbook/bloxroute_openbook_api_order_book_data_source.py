import asyncio
import time
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Optional

from bxsolana.provider import GrpcProvider
from bxsolana_trader_proto import GetOrderbookResponse, GetOrderbooksStreamResponse

from hummingbot.connector.exchange.bloxroute_openbook.bloxroute_openbook_constants import OPENBOOK_PROJECT
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

if TYPE_CHECKING:
    from hummingbot.connector.exchange.bloxroute_openbook.bloxroute_openbook_exchange import BloxrouteOpenbookExchange

class BloxrouteOpenbookAPIOrderBookDataSource(OrderBookTrackerDataSource):
    HEARTBEAT_TIME_INTERVAL = 30.0
    TRADE_STREAM_ID = 1
    DIFF_STREAM_ID = 2
    ONE_HOUR = 60 * 60

    _logger: Optional[HummingbotLogger] = None

    def __init__(self, provider: GrpcProvider, trading_pairs: List[str], connector: 'BloxrouteOpenbookExchange'):
        super().__init__(trading_pairs)

        self._provider = provider
        self._connector = connector
        self._orderbook_stream: Optional[AsyncGenerator[GetOrderbooksStreamResponse, None]] = None

    async def get_last_traded_prices(self,
                                     trading_pairs: List[str],
                                     domain: Optional[str] = None) -> Dict[str, float]:
        raise

    async def _request_order_book_snapshots(self, output: asyncio.Queue):
        raise Exception("""this function is not needed for bloxroute_openbook data source
                           the request is handled in the _order_book_snapshot func""")

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        """
        Retrieves a copy of the full order book from the exchange, for a particular trading pair.

        :param trading_pair: the trading pair for which the order book will be retrieved

        :return: the response from the exchange (JSON dictionary)
        """
        orderbook: GetOrderbookResponse = await self._provider.get_orderbook(market=trading_pair,
                                                                             limit=1,
                                                                             project=OPENBOOK_PROJECT)

        snapshot_timestamp: float = time.time()

        order_book_message_content = {
            "trading_pair": trading_pair,
            "update_id": int(time.time()),
            "bids": [(bid.price, bid.size) for bid in orderbook.bids],
            "asks": [(ask.price, ask.size) for ask in orderbook.asks]
        }
        return OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            order_book_message_content,
            snapshot_timestamp
        )

    async def _connected_websocket_assistant(self) -> WSAssistant:
        await self._provider.connect()
        return WSAssistant()

    async def _subscribe_channels(self, ws: WSAssistant):
        """
        Subscribes to the trade events and diff orders events through the provided websocket connection.
        :param ws: the websocket assistant used to connect to the exchange
        """
        raise

    def _channel_originating_message(self, event_message: Dict[str, Any]) -> str:
        raise Exception("Bloxroute Openbook does not use `_channel_originating_message`")

    async def _process_websocket_messages(self, _: WSAssistant):
        raise

    async def _parse_order_book_snapshot_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise

    async def _parse_order_book_diff_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise Exception("Bloxroute Openbook does not use orderbook diffs")

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise Exception("Bloxroute Openbook does not use trade updates")

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        raise Exception("Bloxroute Openbook does not use orderbook diffs")

    async def listen_for_trades(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        raise Exception("Bloxroute Openbook does not use trades")

    async def _on_order_stream_interruption(self, websocket_assistant: Optional[WSAssistant] = None):
        raise
