# Copyright 2022 Two Sigma Open Source, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from app.defaults import InternalDefaults, AuthenticationOptions
from requests_kerberos import HTTPKerberosAuth, DISABLED
from typing import Any, Union, Tuple
import multiprocessing
import structlog
import requests
import base64
import time
import json
import os


class SensuGoHelper:
    """An object for interacting with Sensu's backend API."""

    BASIC_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
    API_VERSION = "core/v2"

    def __init__(self, state: dict) -> None:
        """Initialize SensuGoHelper with configuration state."""

        self.state = state
        self.logger = structlog.get_logger(InternalDefaults.APPNAME)
        self.auth_method = self.get_authentication_method()

    def get_authentication_method(self) -> AuthenticationOptions:
        """Automatically discovery best authentication method."""

        if self.state.get("sensu_api_key"):
            return AuthenticationOptions.API_KEY_AUTH

        if os.environ.get("SENSU_API_KEY"):
            return AuthenticationOptions.API_KEY_AUTH

        if os.environ.get("KRB5CCNAME"):
            return AuthenticationOptions.KERBEROS_AUTH

        return AuthenticationOptions.BASIC_AUTH

    def get_sensu_api_key(self) -> str:
        return self.state.get("sensu_api_key", os.environ.get("SENSU_API_KEY", ""))

    def get_username(self) -> str:
        """Try to get the correct Sensu username. Fall back to OS username"""
        if "username" in self.state:
            return self.state["username"]

        access_token = self.safe_get_auth_value("access_token", None)
        if access_token:
            claims = access_token.split(".")[1].encode()
            decoded = base64.b64decode(claims + b"=" * (-len(claims) % 4))
            decoded_json = json.loads(decoded.decode())
            if "sub" in decoded_json:
                return decoded_json["sub"]
        return os.getlogin()

    def safe_get_auth_value(self, key: str, default: Any) -> Any:
        """Safely get the 'auth' data from state.

        Returns the auth configuration data as a dict object.
        """

        return self.state.get("auth", {}).get(key, default)

    def url(self) -> str:
        """Parse the url from the state data.

        Return the URL with the trailing slash removed as a string.
        """

        return self.state["url"].strip("/")

    def namespace(self) -> str:
        """Returns the Sensu namespace from state configuration as a string."""

        return self.state.get("namespace", "")

    def auth_headers(self) -> dict:
        """Adds the Authorization header to the request headers.

        Returns HTTP request headers as a dict object.
        """

        auth_headers = self.BASIC_HEADERS.copy()
        if self.auth_method is not AuthenticationOptions.API_KEY_AUTH:
            access_token = self.safe_get_auth_value("access_token", "")
            auth_headers["Authorization"] = f"Bearer {access_token}"
        else:
            sensu_api_key = self.get_sensu_api_key()
            auth_headers["Authorization"] = f"Key {sensu_api_key}"

        return auth_headers

    def get_namespaces(self) -> dict:
        """Get namespaces from Sensu backend.

        Returns the response from the Sensu Backend as a dict object.
        """

        r = self.__request(
            method="get",
            uri=f"{self.url()}/api/{self.API_VERSION}/namespaces",
            headers=self.auth_headers(),
        )
        r.raise_for_status()
        return r.json()

    def __request(
        *args,
        method: str = None,
        uri: str = None,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        auth: Union[list, HTTPKerberosAuth] = None,
        json_data: dict = None,
    ) -> requests.Response:
        """Create and send an HTTP request.

        Returns the response object after the request has been completed.
        """

        action = getattr(requests, method.lower(), None)
        self = args[0]
        self.logger.debug(
            "SensuGoHelper.__request",
            method=method,
            uri=uri,
            headers=headers,
            params=params,
            data=data,
            auth=auth,
            json_data=json_data,
        )
        return action(
            url=uri,
            headers=headers,
            params=params,
            data=data,
            verify=self.state.get("verify_certs", None),
            auth=auth,
            json=json_data,
        )

    def execute_check(self, check_data: dict) -> dict:
        check_name = check_data["check"]
        path = (
            f"{self.url()}/api/{self.API_VERSION}/namespaces/"
            f"{self.namespace()}/checks/{check_name}/execute"
        )

        r = self.__request(
            method="post", uri=path, headers=self.auth_headers(), json_data=check_data
        )
        r.raise_for_status()
        return r.json()

    def get_event(self, entity: str, check: str) -> dict:
        path = (
            f"{self.url()}/api/{self.API_VERSION}/namespaces/"
            f"{self.namespace()}/events/{entity}/{check}"
        )
        r = self.__request(method="get", uri=path, headers=self.auth_headers())
        r.raise_for_status()
        return r.json()

    def new_silence(self, entry, reason) -> int:
        subscription = entry[: entry.rindex(":")]
        check = entry[entry.rindex(":") + 1 :]
        silenced = {
            "metadata": {
                "name": entry,
                "namespace": self.namespace(),
                "labels": None,
                "annotations": None,
            },
            "expire": -1,
            "expire_on_resolve": False,
            "creator": self.get_username(),
            "reason": reason,
            "subscription": subscription,
            "begin": int(time.time()),
        }
        if check != "*":
            silenced["check"] = check
        path = (
            f"{self.url()}/api/{self.API_VERSION}/namespaces/"
            f"{self.namespace()}/silenced"
        )
        r = self.__request(
            method="post", uri=path, headers=self.auth_headers(), json_data=silenced
        )
        r.raise_for_status()
        return r.status_code

    def delete_silence(self, entry: str) -> int:
        path = (
            f"{self.url()}/api/{self.API_VERSION}/namespaces/"
            f"{self.namespace()}/silenced/{entry}"
        )
        r = self.__request(method="delete", uri=path, headers=self.auth_headers())
        r.raise_for_status()
        return r.status_code

    def update_event(self, event: dict) -> int:
        entity_name = event["entity"]["metadata"]["name"]
        check_name = event["check"]["metadata"]["name"]

        path = (
            f"{self.url()}/api/{self.API_VERSION}/namespaces/"
            f"{self.namespace()}/events/{entity_name}/{check_name}"
        )
        r = self.__request(
            method="put", uri=path, headers=self.auth_headers(), json_data=event
        )
        r.raise_for_status()
        return r.status_code

    def resource_fetch_request(
        self,
        resource: str = "events",
        fieldSelector: str = "",
        labelSelector: str = "",
        sensu_continue: Union[str, None] = None,
        limit: int = 100,
    ) -> Tuple[dict, str]:
        """Higher level API request function.

        This function wraps __request and applies various headers
        and parameters as supplied by the user.
        """

        params = {
            "fieldSelector": fieldSelector,
            "labelSelector": labelSelector,
            "limit": limit,
        }
        if sensu_continue:
            params["continue"] = sensu_continue
        r = self.__request(
            method="get",
            uri=(
                f"{self.url()}/api/{self.API_VERSION}/namespaces/"
                f"{self.namespace()}/{resource}"
            ),
            headers=self.auth_headers(),
            params=params,
        )
        continue_key = r.headers.get("Sensu-Continue", None)
        r.raise_for_status()
        return (r.json(), continue_key)

    def multi_resource_fetch_request(self, q: multiprocessing.Queue, **kwargs) -> None:
        """Multiprocess version of resource_fetch_request.

        This function is meant to be the target of a Process.
        Make a backend API request to Sensu and put the response on a shared
        Queue object to be processed by the main application processs.
        """

        self.logger.debug("SensuGoHelper.multi_resource_fetch_request", **kwargs)
        try:
            q.put((None, self.resource_fetch_request(**kwargs)))
        except requests.exceptions.HTTPError as e:
            q.put((e, {}))

    def get_auth_value(
        self, username: str = None, password: str = None
    ) -> Union[Tuple, HTTPKerberosAuth, None]:
        if self.auth_method == AuthenticationOptions.KERBEROS_AUTH:
            return HTTPKerberosAuth(mutual_authentication=DISABLED)
        elif self.auth_method == AuthenticationOptions.BASIC_AUTH:
            return (username, password)
        else:
            # This condition should not be possible
            return None

    def authenticate(self, username: str = None, password: str = None) -> dict:
        """Make a request with credentials to receive an access token."""

        auth = self.get_auth_value(username, password)
        if not auth:
            return

        r = self.__request(
            method="get",
            uri=f"{self.url()}/auth",
            headers=self.BASIC_HEADERS,
            auth=auth,
        )
        r.raise_for_status()
        return r.json()

    def auth_test(self, username: str = None, password: str = None) -> bool:
        """Tests if credentials are valid."""

        auth = self.get_auth_value(username, password)
        if not auth:
            return

        r = self.__request(method="get", uri=f"{self.url()}/auth/test", auth=auth)
        if r.status_code != 200:
            return False
        return True

    def is_token_expired(self) -> bool:
        """Checks if the JWT is expired."""

        expires_at = self.safe_get_auth_value("expires_at", 0)
        now = int(time.time())
        if (expires_at - now) <= 10:
            return True
        return False

    def refresh(self) -> dict:
        """Use the refresh token to get a new access token."""

        refresh_token = self.safe_get_auth_value("refresh_token", "")
        r = self.__request(
            method="post",
            uri=f"{self.url()}/auth/token",
            headers=self.auth_headers(),
            json_data={"refresh_token": refresh_token},
        )
        r.raise_for_status()
        return r.json()
