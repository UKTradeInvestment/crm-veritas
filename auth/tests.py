import jwt

from unittest import TestCase, mock
from urllib.parse import quote, urlparse

from ukti.datahub.auth import app
from ukti.datahub.auth import veritas


class BastionTestCase(TestCase):

    def setUp(self):

        veritas.CLIENT_ID = "client-id"
        veritas.AUTH_SERVER = "http://localhost:5000"
        veritas.AUTH_SECRET = "secret"

        app.config['TESTING'] = True
        app.secret_key = "secret"

        self.auth = app.test_client()

    def test_index_no_next(self):
        self.assertEqual(self.auth.get("/").status_code, 400, "/")

    def test_index(self):

        r = self.auth.get("/?next={}".format(
            quote("http://localhost:5001/", safe="")))

        self.assertEqual(r.status_code, 302)

        query_args = urlparse(r.headers["Location"]).query.split("&")
        self.assertTrue("response_type=code" in query_args)
        self.assertTrue("client_id=client-id" in query_args)
        url = quote(veritas.AUTH_SERVER, safe="")
        self.assertTrue("redirect_uri={}%2Foauth2".format(url) in query_args)

    def test_oauth2_no_code(self):
        r = self.auth.get("/oauth2?session_state=some-string")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers["Location"], "/")

    def test_oauth2_no_state(self):
        r = self.auth.get("/oauth2?code=some-string")
        self.assertEqual(r.status_code, 403)

    def test_oauth2_no_session_state(self):
        r = self.auth.get("/oauth2?code=some-string&state=invalid")
        self.assertEqual(r.status_code, 403)

    def test_oauth2_invalid_state(self):
        session = {"next": "http://nowhere.ca/", "state": "some-state"}
        with mock.patch("ukti.datahub.auth.flask.session", new=session):
            r = self.auth.get("/oauth2?code=some-string&state=invalid")
            self.assertEqual(r.status_code, 403)

    def test_oauth2(self):
        session = {"next": "http://nowhere.ca/", "state": "some-state"}
        with mock.patch("ukti.datahub.auth.flask.session", new=session):
            r = self.auth.get("/oauth2?code=some-string&state=some-state")
            self.assertEqual(r.status_code, 302)
            self.assertEqual(r.headers["Location"], session["next"])
            self.assertEqual(
                jwt.decode(
                    r.cookies[veritas.COOKIE],
                    veritas.AUTH_SECRET
                )["code"],
                "some-string"
            )
