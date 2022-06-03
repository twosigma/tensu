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

from datetime import datetime
from unittest import mock
import app
from app.sensu_go import SensuGoHelper
from app.defaults import AuthenticationOptions
from requests import Response
import unittest
import logging
import sys
from requests import HTTPError


class SensuGoHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        logging.basicConfig(stream=sys.stderr)
        self.logger = logging.getLogger(self.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.fake_access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NTQwMDk5MjcsImp0aSI6IjlkZWZkMWM2OTc5YjcyMWRmNDk2ZmJjODYzNDIxMTE5IiwiaXNzIjoiaHR0cDovL215LXNlbnN1LXNlcnZlci5jb20iLCJzdWIiOiJ1c2VyLWZyb20tand0IiwiZ3JvdXBzIjpbInNlY2luZnJhLWFkIiwic3lzdGVtOnVzZXJzIl0sInByb3ZpZGVyIjp7InByb3ZpZGVyX2lkIjoiYmFzaWMiLCJwcm92aWRlcl90eXBlIjoiIiwidXNlcl9pZCI6InVzZXItZnJvbS1qd3QifSwiYXBpX2tleSI6ZmFsc2V9.YxASxU-0P89FCvhkE05Aew05_1yWzns7ncHU-3sMVtU"

    def fake_api_response(self, content, status_code=200, headers={}):
        r = Response()
        r.status_code = status_code
        r.headers = headers
        r._content = content.encode()
        return r

    def test_get_authentication_method_api_key_from_state(self):
        sensu_go_helper = SensuGoHelper({"sensu_api_key": "abc213"})
        assert (
            sensu_go_helper.get_authentication_method()
            == AuthenticationOptions.API_KEY_AUTH
        )

    @mock.patch("os.environ", new={"SENSU_API_KEY": "ABC123"})
    def test_get_authentication_method_api_key_from_environ(self):
        sensu_go_helper = SensuGoHelper({})
        assert (
            sensu_go_helper.get_authentication_method()
            == AuthenticationOptions.API_KEY_AUTH
        )

    @mock.patch("os.environ", new={"KRB5CCNAME": "ABC123"})
    def test_get_authentication_method_krb_from_environ(self):
        sensu_go_helper = SensuGoHelper({})
        assert (
            sensu_go_helper.get_authentication_method()
            == AuthenticationOptions.KERBEROS_AUTH
        )

    @mock.patch("os.environ", new={})
    def test_get_authentication_method_krb_from_environ(self):
        sensu_go_helper = SensuGoHelper({})
        assert (
            sensu_go_helper.get_authentication_method()
            == AuthenticationOptions.BASIC_AUTH
        )

    def test_get_sensu_api_key_from_state(self):
        sensu_go_helper = SensuGoHelper({"sensu_api_key": "abc123"})
        assert sensu_go_helper.get_sensu_api_key() == "abc123"

    @mock.patch("os.environ", new={"SENSU_API_KEY": "ABC123"})
    def test_get_sensu_api_key_from_environ(self):
        sensu_go_helper = SensuGoHelper({})
        assert sensu_go_helper.get_sensu_api_key() == "ABC123"

    def test_get_username_from_state(self):
        sensu_go_helper = SensuGoHelper({"username": "user1"})
        assert sensu_go_helper.get_username() == "user1"

    def test_get_username_from_jwt(self):
        sensu_go_helper = SensuGoHelper(
            {"auth": {"access_token": self.fake_access_token}}
        )
        assert sensu_go_helper.get_username() == "user-from-jwt"

    @mock.patch("os.getlogin", return_value="user-from-sys")
    def test_get_username_from_os(self, m):
        sensu_go_helper = SensuGoHelper({})
        assert sensu_go_helper.get_username() == "user-from-sys"

    def test_safe_get_auth_value_exists(self):
        sensu_go_helper = SensuGoHelper({"auth": {"access_token": "foobar"}})
        assert sensu_go_helper.safe_get_auth_value("access_token", "baz") == "foobar"

    def test_safe_get_auth_value_absent(self):
        sensu_go_helper = SensuGoHelper({"auth": {"no_access_token": "foobar"}})
        assert sensu_go_helper.safe_get_auth_value("access_token", "baz") == "baz"

    def test_get_url(self):
        sensu_go_helper = SensuGoHelper({"url": "https://foo-bar.com/baz/"})
        assert sensu_go_helper.url() == "https://foo-bar.com/baz"

    def test_get_namespace(self):
        sensu_go_helper = SensuGoHelper({"namespace": "default"})
        assert sensu_go_helper.namespace() == "default"

    def test_auth_headers_bearer(self):
        sensu_go_helper = SensuGoHelper(
            {"auth": {"access_token": self.fake_access_token}}
        )
        assert (
            sensu_go_helper.auth_headers()["Authorization"]
            == f"Bearer {self.fake_access_token}"
        )

    @mock.patch("os.environ", new={"SENSU_API_KEY": "ABC123"})
    def test_auth_headers_key(self):
        sensu_go_helper = SensuGoHelper({})
        assert sensu_go_helper.auth_headers()["Authorization"] == "Key ABC123"

    def test_namespaces_200(self):
        r = self.fake_api_response('[ {"name": "default"}, {"name": "other"} ]')
        with mock.patch.object(
            SensuGoHelper, "_SensuGoHelper__request", return_value=r
        ) as m:

            sensu_go_helper = SensuGoHelper(
                {"sensu_api_key": "abc123", "url": "https://my-sensu-go:8080/"}
            )
            assert sensu_go_helper.get_namespaces()[0]["name"] == "default"

    def test_namespaces_400(self):
        r = self.fake_api_response('[ {"name": "default"}, {"name": "other"} ]', status_code=400)
        with mock.patch.object(
            SensuGoHelper, "_SensuGoHelper__request", return_value=r
        ) as m:

            sensu_go_helper = SensuGoHelper(
                {"sensu_api_key": "abc123", "url": "https://my-sensu-go:8080/"}
            )
            self.assertRaises(HTTPError, sensu_go_helper.get_namespaces)

    @mock.patch("app.sensu_go.requests.get")
    def test_request(self, m):
        sensu_go_helper = SensuGoHelper({})
        sensu_go_helper._SensuGoHelper__request(
            method="get",
            uri="https://my-sensu-go:8080/",
            headers={"X-Header-1": "FooBar"},
            params=None,
            data=None,
            auth=("username", "password"),
            json_data=None,
        )
        m.assert_called_once_with(
            auth=("username", "password"),
            data=None,
            headers={"X-Header-1": "FooBar"},
            json=None,
            params=None,
            url="https://my-sensu-go:8080/",
            verify=None,
        )
