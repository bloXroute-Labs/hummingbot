import bxsolana.provider.constants as constants
import bxsolana_trader_proto as proto

EXCHANGE_NAME = "bloxroute_openbook"
SPOT_OPENBOOK_PROJECT = proto.Project.P_OPENBOOK

TESTNET_PROVIDER_ENDPOINT = constants.TESTNET_API_WS
MAINNET_PROVIDER_ENDPOINT = "ws://54.163.206.248:1809/ws"

CLIENT_ORDER_ID_MAX_LENGTH = 10
ORDERBOOK_RETRIES = 5
