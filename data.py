import dateutil.parser

import flask
import jwt
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv

from common import HEADER_NAME

# Tap veritas.conf if it's available
if os.path.exists("/etc/veritas.conf"):
    load_dotenv("/etc/veritas.conf")

AUTH_SECRET = os.getenv("VERITAS_AUTH_SECRET")
BASTION_SECRET = os.getenv("VERITAS_BASTION_SECRET")
FORCE_REAUTH = 8  # After n hours, force a re-authentication


app = flask.Flask(__name__)


class TokenVerificationError(Exception):
    pass


def verify_tokens():

    bastion = verify_token(flask.request.headers, HEADER_NAME, BASTION_SECRET)
    auth = verify_token(bastion, "token", AUTH_SECRET)

    # Recreate nested token

    new_expires = (datetime.utcnow() + timedelta(minutes=30)).isoformat()

    auth["expires"] = new_expires
    bastion["expires"] = new_expires

    bastion["token"] = jwt.encode(auth, AUTH_SECRET)

    return jwt.encode(bastion, BASTION_SECRET)


def verify_token(token, key, secret):

    # No cookie: fail
    if key not in token:
        raise TokenVerificationError("No token found")

    # No token: fail
    try:
        decoded = jwt.decode(token, secret)
    except jwt.InvalidTokenError:
        raise TokenVerificationError("No valid token found")

    # Expired token? > You need to re-authenticate.
    if datetime.now() > dateutil.parser.parse(decoded["expires"]):
        raise TokenVerificationError("Token expired")

    # Even with a valid token, we force a re-auth every few hours.
    created = dateutil.parser.parse(decoded["created"])
    if (datetime.now() - created).total_seconds() > 60 * 60 * FORCE_REAUTH:
        raise TokenVerificationError("Token creation time is too old")

    return decoded


@app.route('/endpoint')
def endpoint():

    return_token = verify_tokens()

    response = flask.jsonify({"this": "is", "an": "arbitrary response"})
    response.headers[HEADER_NAME] = return_token

    return response


if __name__ == '__main__':
    app.secret_key = "secret"
    app.run(debug=True, port=5002)
