import jwt
import requests
import os
import uuid

from dotenv import load_dotenv


# Tap the environment file if it's available
if os.path.exists("/etc/veritas.conf"):
    load_dotenv("/etc/veritas.conf")


class TokenError(Exception):

    def __init__(self, message, status_code=400, *args, **kwargs):
        self.status_code = status_code
        Exception.__init__(self, *tuple([message] + list(args)), **kwargs)


class Veritas(object):

    __version__ = (0, 0, 1)

    # Some of these may be null depending on the environment
    AUTH_SERVER = os.getenv("AUTH_SERVER")
    AUTH_SECRET = os.getenv("AUTH_SECRET")
    DATA_SERVER = os.getenv("DATA_SERVER")
    DATA_SECRET = os.getenv("DATA_SECRET")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    APP_TOKEN = os.getenv("APP_TOKEN")

    HEADER_NAME = "X-Cerebro-Token"
    COOKIE = "veritas"
    SESSION = "session"
    TOKEN = "token"

    AZURE = "https://login.microsoftonline.com"
    AZURE_AUTHORISE = "{}/common/oauth2/authorize".format(AZURE)
    AZURE_TOKEN = "{}/{}/oauth2/token".format(AZURE, APP_TOKEN)
    REDIRECT_URI = "{}/{}".format(AUTH_SERVER, "oauth2")

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

    # Auth

    def get_auth_url(self, state):
        """
        Strictly speaking, the `state` parameter is optional, but as it
        protects against XSS attacks, we're making it mandatory here.

        :param state:         (str) A random string, verified by the auth
                                    server when Azure bounces the user back
                                    there.
        """
        return requests.Request("GET", self.AZURE_AUTHORISE, params={
            "response_type": "code",
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "state": state
        }).prepare().url

    def get_auth_cookie(self, code):
        """
        Set the auth cookie before sending the response to the user.

        :param code:     (str)      The big long string that Azure sends back
                                    along with the client to the auth server.
        """
        return jwt.encode(
            {"code": code, "nonce": str(uuid.uuid4())},
            self.AUTH_SECRET
        )

    # Bastion

    def get_bastion_redirect_url(self, nxt):
        """
        The URL we bounce users too if they don't have a cookie.  Strictly
        speaking, this shouldn't happen because users should never come directly
        to the bastion, but it's entirely likely that the UI will hit a bastion
        URL as a means of testing whether the user has a cookie or not.

        :param nxt: (str) The URL you want the user to return to after she's
                          been authenticated.  Typically, this is the URL
                          they're trying to visit on the bastion host.
        """
        return requests.Request("GET", self.AUTH_SERVER, params={
            "next": "{}{}".format(self.bastion_server, nxt)
        }).prepare().url

    def get_data_response(self, path, args, token):
        """
        Hit the data server with the request that hit the bastion server, taking
        care to include a header with the right auth data, signed by the bastion
        server.
        :param path: (str) The URL path
        :param args: (dict) The arguments (if any)
        :param token: (str) The jwt for auth on the data end
        """
        return requests.get(
            self.DATA_SERVER + path,
            params=args,
            headers={
                self.HEADER_NAME: jwt.encode(
                    {self.TOKEN: token},
                    self.bastion_secret
                )
            }
        )

    # Data

    def get_token_from_headers(self, headers):
        """
        Try to find and decode the auth token data in the request header.

        :param headers: A dictionary of headers in the request.
        """

        # No header: fail
        if self.HEADER_NAME not in headers:
            raise TokenError("No bastion token specified", status_code=403)

        try:
            return jwt.decode(headers[self.HEADER_NAME], self.bastion_secret)
        except jwt.InvalidTokenError:
            raise TokenError("No valid bastion token found")

    def get_identity_from_nested_token(self, bastion):
        """
        This method isn't always necessary, as most requests will contain a
        session value rather than an auth token.  The first request however will
        only contain an auth token, so the data server will need to validate it
        against the Azure AD web service and return some identity information
        from what it finds there.

        :param bastion: (dict) The decoded jwt from the bastion request
        """

        if "token" not in bastion:
            raise TokenError("The bastion token was malformed")

        try:
            auth = jwt.decode(bastion[self.TOKEN], self.AUTH_SECRET)
        except jwt.InvalidTokenError:
            raise TokenError("No valid auth token found")

        if "code" not in auth:
            raise TokenError("The auth token was malformed")

        # Get user data from Azure
        response = requests.post(self.AZURE_TOKEN, {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "code": auth["code"],
            "grant_type": "authorization_code",
            "redirect_uri": self.REDIRECT_URI,
            "resource": "https://graph.windows.net"
        })

        if response.status_code >= 300:
            raise TokenError(response.text, response.status_code)

        # Parse that user data for useful information
        return jwt.decode(response.json()["id_token"], verify=False)
