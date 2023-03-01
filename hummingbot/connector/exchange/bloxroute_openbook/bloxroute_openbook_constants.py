import bxsolana.provider.constants as constants
import bxsolana_trader_proto as proto

EXCHANGE_NAME = "bloxroute_openbook"
SPOT_OPENBOOK_PROJECT = proto.Project.P_OPENBOOK

PROVIDER_ENDPOINT = constants.TESTNET_API_WS

CLIENT_ORDER_ID_MAX_LENGTH = 7
ORDERBOOK_RETRIES = 2
