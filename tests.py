import os
import unittest
import veritas


class VeritasTest(unittest.TestCase):

    def setUp(self):

        os.environ["AUTH_SERVER"] = "http://localhost:5000"
        os.environ["BASTION_SERVER"] = "http://localhost:5001"
        os.environ["DATA_SERVER"] = "http://localhost:5002"

        os.environ["AUTH_SECRET"] = "auth-secret"
        os.environ["BASTION_SECRET"] = "bastion-secret"

        os.environ["CLIENT_ID"] = "client-id"
        os.environ["CLIENT_SECRET"] = "client-secret"

        os.environ["APP_TOKEN"] = "app-token"

    def test_get_auth_url(self):
        v = veritas.Veritas()
        self.assertEqual(
            v.get_auth_url("state"),
            "https://login.microsoftonline.com/common/oauth2/authorize?response_type=code&client_id=client-id&redirect_uri=http%3A//localhost%3A5000/oauth2%0A&state=state"
        )
