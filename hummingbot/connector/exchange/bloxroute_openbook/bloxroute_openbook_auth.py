<<<<<<< HEAD
from typing import Dict
import json

from bxsolana import provider
=======
import hashlib
import hmac
import json
from collections import OrderedDict
from typing import Any, Dict
from urllib.parse import urlencode
>>>>>>> origin/Files_For_Bloxroute_Openbook

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
<<<<<<< HEAD
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest
from hummingbot.connector.time_synchronizer import TimeSynchronizer


class BloxrouteOpenbookAuth(AuthBase):
    """
    Auth class required to use bloxRoute Labs Solana Trader API
    Needed for web assistants factory
    """

    def __init__(self, auth_header: str, time_provider: TimeSynchronizer):
        self.auth_header = auth_header
        self.time_provider: TimeSynchronizer = time_provider
=======
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


class BloxrouteOpenbookAuth(AuthBase):
    def __init__(self, api_key: str, secret_key: str, time_provider: TimeSynchronizer):
        self.api_key = api_key
        self.secret_key = secret_key
        self.time_provider = time_provider
>>>>>>> origin/Files_For_Bloxroute_Openbook

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the server time and the signature to the request, required for authenticated interactions. It also adds
        the required parameter in the request header.
        :param request: the request to be configured for authenticated interaction
        """
        if request.method == RESTMethod.POST:
            request.data = self.add_auth_to_params(params=json.loads(request.data))
        else:
            request.params = self.add_auth_to_params(params=request.params)

        headers = {}
        if request.headers is not None:
            headers.update(request.headers)
        headers.update(self.header_for_authentication())
        request.headers = headers

<<<<<<< HEAD
        headers = {}
        if request.headers is not None:
            headers.update(request.headers)
        headers.update(self.authentication_headers(request=request))
        request.headers = headers

        print("blox route auth header")
        print(self.auth_header)

=======
>>>>>>> origin/Files_For_Bloxroute_Openbook
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        This method is intended to configure a websocket request to be authenticated. Binance does not use this
        functionality
        """
<<<<<<< HEAD

        return request  # pass-through
=======
        return request  # pass-through

    def add_auth_to_params(self,
                           params: Dict[str, Any]):
        timestamp = int(self.time_provider.time() * 1e3)

        request_params = OrderedDict(params or {})
        request_params["timestamp"] = timestamp

        signature = self._generate_signature(params=request_params)
        request_params["signature"] = signature

        return request_params

    def header_for_authentication(self) -> Dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    def _generate_signature(self, params: Dict[str, Any]) -> str:

        encoded_params_str = urlencode(params)
        digest = hmac.new(self.secret_key.encode("utf8"), encoded_params_str.encode("utf8"), hashlib.sha256).hexdigest()
        return digest
>>>>>>> origin/Files_For_Bloxroute_Openbook
