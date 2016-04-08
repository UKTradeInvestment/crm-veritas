import os

from unittest import TestCase

from ukti.datahub.bastion import app


class BastionTestCase(TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

        os.environ["BASTION_SERVER"] = "http://localhost:5001"
        os.environ["BASTION_SECRET"] = "secret"

    def test_authentication_process(self):
        """
        A sort of test-driven way to document the entire authentication process.
        """

        # 1. User visits the UI where we make the first request to the bastion
        #    host for user data.  This request should be rejected of course,
        #    since we presently don't have any cookie containing session data.

        for url in ("/", "/anything", "/anything/else", "/asdf?jkl=semicolon"):
            r = self.app.get(url)
            self.assertEqual(r.status_code, 400, url)
            self.assertEqual(r.data.split()[-1], "x", url)