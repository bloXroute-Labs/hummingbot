import math
from decimal import Decimal
from typing import Any, Dict

import bxsolana_trader_proto.api as api
import bxsolana_trader_proto.common as common
from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap, ClientFieldData
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import OrderState
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

EXAMPLE_PAIR = "SOL-USDC"

DEFAULT_FEES = TradeFeeSchema(
    buy_percent_fee_deducted_from_returns=True,
    maker_percent_fee_decimal=Decimal("0.002"),
    taker_percent_fee_decimal=Decimal("0.002"),
)


class BloXrouteConnectorMap(BaseConnectorConfigMap):
    connector: str = Field(default="bloxroute_openbook", client_data=None)
    bloxroute_auth_header: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter bloxroute Labs authorization header",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )

    solana_wallet_private_key: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your solana wallet private key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )

    class Config:
        title = "bloxroute_openbook"


KEYS = BloXrouteConnectorMap.construct()


def trade_type_to_side(trade_type: TradeType) -> api.Side:
    if trade_type == TradeType.BUY:
        return api.Side.S_BID
    elif trade_type == TradeType.SELL:
        return api.Side.S_ASK
    else:
        return api.Side.S_UNKNOWN


def order_type_to_blxr_order_type(order_type: OrderType) -> common.OrderType:
    if order_type == OrderType.MARKET:
        return common.OrderType.OT_MARKET
    elif order_type == OrderType.LIMIT:
        return common.OrderType.OT_LIMIT
    else:
        raise Exception(f"unknown order type {order_type.value}")
