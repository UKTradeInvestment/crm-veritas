import json
import os

from unittest import TestCase
from urllib.parse import quote

from ukti.datahub.auth import app as auth_app
from ukti.datahub.bastion import app as bastion_app


class BastionTestCase(TestCase):

    AUTH_SERVER = "http://localhost:5000"
    BASTION_SERVER = "http://localhost:5001"
    BASTION_SECRET = "secret"

    def setUp(self):

        os.environ["AUTH_SERVER"] = self.AUTH_SERVER
        os.environ["BASTION_SERVER"] = self.BASTION_SERVER
        os.environ["BASTION_SECRET"] = self.BASTION_SECRET

        auth_app.config['TESTING'] = True
        bastion_app.config['TESTING'] = True

        self.auth = auth_app.test_client()
        self.bastion = bastion_app.test_client()

    def test_authentication_process(self):
        """
        A sort of test-driven way to document the entire authentication process.
        """

        # 1. User visits the UI where we make the first request to the bastion
        #    host for user data.  This request should be rejected of course,
        #    since we presently don't have any cookie containing session data.

        url = "/path/to/something"
        r = self.bastion.get(url)
        self.assertEqual(r.status_code, 400, url)
        self.assertEqual(
            json.loads(r.get_data().decode("utf-8"))["message"],
            "{}/?next={}{}".format(
                self.AUTH_SERVER,
                quote(self.BASTION_SERVER, safe=""),
                quote(url, safe="")
            ),
            url
        )

        # 2. The bastion server dropped a 400 bomb, rejecting the request on
        #    account of the fact that a cookie wasn't included, so we redirect
        #    the user to the URL in the Bastion server's response, which is to
        #    say that we bounce the user to the auth server, with a next= value
        #    so we know where to return them when they're ready.

        r = self.auth.get("/?next={}".format(
            quote(self.BASTION_SERVER, safe="")))
