import jwt
import requests
import os
import uuid

from dotenv import load_dotenv


# Tap the environment file if it's available
if os.path.exists(".env"):
    load_dotenv(".env")


class Veritas(object):

    AZURE = "https://login.microsoftonline.com"
    AZURE_AUTHORISE = "{}/common/oauth2/authorize".format(AZURE)

    # Some of these may be null depending on the environment
    AUTH_SERVER = os.getenv("AUTH_SERVER")
    AUTH_SECRET = os.getenv("AUTH_SECRET")
    DATA_SERVER = os.getenv("DATA_SERVER")
    DATA_SECRET = os.getenv("DATA_SECRET")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    HEADER_NAME = "X-Cerebro-Token"
    COOKIE = "veritas"

    def __init__(self, bastion_server=None, bastion_secret=None):
        """
        While there's only ever one instance of the auth server, there can be n
        bastion servers, so we allow the instance to be created with dynamic
        bastion values.

        :param bastion_server: (str) The URL for the bastion server.  Typically
                                     something like https://mysite.com (note
                                     the absence of a trailing slash).
        :param bastion_secret: (str) The secret key for the bastion host.
        """
        self.bastion_server = bastion_server
        self.bastion_secret = bastion_secret

    def get_auth_url(self, state, redirect_path):
        """
        Strictly speaking, the `state` parameter is optional, but as it
        protects against XSS attacks, we're making it mandatory here.

        :param state:         (str) A random string, verified by the auth
                                    server when Azure bounces the user back
                                    there.
        :param redirect_path: (str) The URL to which you want Azure to return
                                    the user when it's finished with them.
        """
        return requests.Request("GET", self.AZURE_AUTHORISE, params={
            "response_type": "code",
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.AUTH_SERVER + redirect_path,
            "state": state
        }).prepare().url

    def set_auth_cookie(self, response, code):
        """
        Set the auth cookie before sending the response to the user.

        :param response: (response) A Flask response object
        :param code:     (str)      The big long string that Azure sends back
                                    along with the client to the auth server.
        """
        response.set_cookie(self.COOKIE, jwt.encode({
            "code": code,
            "nonce": str(uuid.uuid4())
        }, self.AUTH_SECRET))

    def get_bastion_redirect_url(self, nxt):
        """
        The URL we bounce users too if they don't have a cookie.

        :param nxt: (str) The URL you want the user to return to after she's
                          been authenticated.  Typically, this is the URL
                          they're trying to visit on the bastion host.
        """
        return requests.Request("GET", self.AUTH_SERVER, params={
            "next": self.bastion_server + nxt
        }).prepare().url
