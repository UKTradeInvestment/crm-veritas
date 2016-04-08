from unittest import TestCase

from bastion import app


class BastionTestCase(TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_authentication_process(self):
        """
        A sort of test-driven way to document the entire authentication process.
        """

        # 1. User visits the UI where we make the first request to the bastion
        #    host for user data.  This request should be rejected of course,
        #    since we presently don't have any cookie containing session data.

        self.assertEqual(self.app.get('/').status_code, 400)