import json
import os

from unittest import TestCase
from urllib.parse import quote

from ukti.datahub.bastion import app as bastion_app


class BastionTestCase(TestCase):

    AUTH_SERVER = "http://localhost:5000"
    BASTION_SERVER = "http://localhost:5001"
    BASTION_SECRET = "secret"

    def setUp(self):

        os.environ["AUTH_SERVER"] = self.AUTH_SERVER
        os.environ["BASTION_SERVER"] = self.BASTION_SERVER

        bastion_app.config['TESTING'] = True

        self.bastion = bastion_app.test_client()

    def test_cookie_rejection(self):

        for url in ("/", "/anything", "/anything/εłσε", "/asdf?jkl=semicolon"):
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
