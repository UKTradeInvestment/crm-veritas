import jwt
import responses

from unittest import TestCase
from urllib.parse import urlparse
from veritas.veritas import Veritas, TokenError


class VeritasTest(TestCase):

    maxDiff = None

    def setUp(self):
        
        self.veritas = Veritas()

        # Force the class variables to something we control for these tests

        self.veritas.AUTH_SERVER = "http://localhost:5000"
        self.veritas.BASTION_SERVER = "http://localhost:5001"
        self.veritas.DATA_SERVER = "http://localhost:5002"

        self.veritas.AUTH_SECRET = "auth-secret"
        self.veritas.BASTION_SECRET = "bastion-secret"

        self.veritas.CLIENT_ID = "client-id"
        self.veritas.CLIENT_SECRET = "client-secret"

        self.veritas.APP_TOKEN = "app-token"

    def test_get_auth_url(self):
        self.assertEqual(
            set(urlparse(self.veritas.get_auth_url("state")).query.split("&")),
            {
                "response_type=code",
                "client_id=client-id",
                "redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Foauth2",
                "state=state"
            }
        )

    def test_get_auth_cookie(self):
        code = "my-code"
        secret = "some secret"
        self.veritas.AUTH_SECRET = secret
        self.assertEqual(
            jwt.decode(self.veritas.get_auth_cookie(code), secret)["code"],
            code
        )

    def test_get_bastion_redirect_url(self):
        self.veritas.bastion_server = "http://localhost:5001"
        self.assertEqual(
            urlparse(self.veritas.get_bastion_redirect_url("/w00t")).query,
            "next={}".format("http%3A%2F%2Flocalhost%3A5001%2Fw00t")
        )

    @responses.activate
    def test_get_identity_from_nested_token(self):

        self.veritas.AUTH_SECRET = "secret"
        self.veritas.AZURE_TOKEN = "{}/app-token/oauth2/token".format(
            self.veritas.AZURE
        )

        responses.add(
            responses.POST,
            "https://login.microsoftonline.com/app-token/oauth2/token",
            body='{"id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvaWQiOj'
                 'EyMywiZmFtaWx5X25hbWUiOiJGYW1pbHkiLCJnaXZlbl9uYW1lIjoiR2l2ZW4'
                 'ifQ.MDfAGcDi7XjNhbLnEkQHexOnbzPsSVbSfBRrjkVT4xI"}',
            status=200,
            content_type='application/json'
        )

        info = self.veritas.get_identity_from_nested_token({
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2RlIjoidGhp"
                     "cyBpcyBhIGNvZGUifQ.piTpeboWlE6pYu7t6hHI2mNECvuLtDNp2R"
                     "AIDDoiJP4"
        })

        self.assertEqual(info["oid"], 123)
        self.assertEqual(info["family_name"], "Family")
        self.assertEqual(info["given_name"], "Given")

        # Expected exceptions
        with self.assertRaises(TokenError):
            self.veritas.get_identity_from_nested_token({"not-a-token": "x"})
        with self.assertRaises(TokenError):
            self.veritas.get_identity_from_nested_token({"token": "broken"})
        with self.assertRaises(TokenError):
            self.veritas.get_identity_from_nested_token({
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub3QiOiJhIHRv"
                         "a2VuIn0.YxSUDNLukXozOo3JbXsr8XvCzAsa13ZK0vtF2nX-wn4"
            })
