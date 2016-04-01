import flask
import jwt
import os
import requests

from dotenv import load_dotenv

from common import HEADER_NAME, AZURE, AUTH_SERVER

# Tap the environment file if it's available
if os.path.exists(".env"):
    load_dotenv(".env")

AUTH_SECRET = os.getenv("AUTH_SECRET")
BASTION_SECRET = os.getenv("BASTION_SECRET")
DATA_SECRET = os.getenv("DATA_SECRET")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
APP_TOKEN = os.getenv("APP_TOKEN")

AZURE_TOKEN = "{}/{}/oauth2/token".format(AZURE, APP_TOKEN)
REDIRECT_URI = "{}/oauth2".format(AUTH_SERVER)

FORCE_REAUTH = 8  # After n hours, force a re-authentication

app = flask.Flask(__name__)


class TokenVerificationError(Exception):
    pass


class User(object):
    """
    This is a demo, so there's no database to speak of.  Imagine this as a
    proper ORM though, where you could conceivably do something like:

      user = Session.objects.get(key="123456789").user
    """

    def __init__(self, azure_id=None, given_name=None, family_name=None):
        """
        For some reason, Micros~1 hasn't figured out that breaking up the name
        field is a Bad Idea.
        """
        self.azure_id = azure_id
        self.given_name = given_name
        self.family_name = family_name

    @classmethod
    def get_from_session(cls, session):
        if session == "123456789":
            return cls(azure_id=3)

    @classmethod
    def create(cls, azure_id, given_name, family_name):
        """Obviously, this doesn't do anything useful."""
        return User(azure_id, given_name, family_name)


def get_mock_response():
    """
    This is just to compile a response with a session id.  Obviously for a
    proper app, this would be where most of the work goes.
    """

    return_token = jwt.encode({"session": "123456789"}, BASTION_SECRET)

    response = flask.jsonify({"this": "is", "an": "arbitrary response"})
    response.headers[HEADER_NAME] = return_token

    return response


@app.route('/arbitrary-endpoint')
def endpoint():

    headers = flask.request.headers

    # No cookie: fail
    if HEADER_NAME not in headers:
        return flask.abort(403, description="No bastion token specified")

    try:
        bastion = jwt.decode(headers[HEADER_NAME], BASTION_SECRET)
    except jwt.InvalidTokenError:
        return flask.abort(400, "No valid bastion token found")

    # If there's a session in the jwt and it resolves to a legit user, we can
    # safely assume that the user is authenticated
    user = User.get_from_session(bastion.get("session"))
    if user:
        return get_mock_response()

    # There's no session in the bastion jwt, so we go looking for a token for
    # the last bits of Azure authentication

    if "token" not in bastion:
        return flask.abort(400, description="The bastion token was malformed")

    try:
        auth = jwt.decode(bastion["token"], AUTH_SECRET)
    except jwt.InvalidTokenError:
        return flask.abort(400, description="No valid auth token found")

    if "code" not in auth:
        return flask.abort(400, description="The auth token was malformed")

    # Get user data from Azure
    response = requests.post(AZURE_TOKEN, {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth["code"],
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "resource": "https://graph.windows.net"
    })

    if response.status_code >= 300:
        return flask.abort(response.status_code, description=response.text)

    # Parse that user data for useful information and dump it into a user
    # model if you like.
    identity = jwt.decode(response.json()["id_token"], verify=False)
    User.create(
        identity["oid"],
        identity["given_name"],
        identity["family_name"]
    )

    return get_mock_response()


if __name__ == '__main__':
    app.secret_key = "secret"
    app.run(debug=True, port=5002)
