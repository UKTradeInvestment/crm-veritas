# App server example

import dateutil.parser
import flask
import jwt
import os

from datetime import datetime, timedelta
from urllib.parse import quote as url_encode

AUTH_SERVER = "http://azure.danielquinn.org:5000/"
APP_SERVER = "http://azure.danielquinn.org:5001/"

SECRET = os.getenv("ATHENA_SECRET", "secret")
COOKIE = "arbiter"
FORCE_REAUTH = 8  # After n hours, force a re-authentication


app = flask.Flask(__name__)


@app.route("/")
def index():

    # We attach `next=` to the redirect so that the auth server knows where it
    # should bounce the user back when everything is finished.
    redirect = flask.redirect("{}?next={}".format(
        AUTH_SERVER,
        url_encode(APP_SERVER)
    ))

    # No cookie? > Go get one.
    if COOKIE not in flask.request.cookies:
        return redirect

    # Bad token? You're probably being evil. > Go get a real one.
    try:
        payload = jwt.decode(flask.request.cookies[COOKIE], SECRET)
    except jwt.InvalidTokenError:
        return redirect

    expires = dateutil.parser.parse(payload["expires"])
    created = dateutil.parser.parse(payload["created"])

    # Expired token? > You need to re-authenticate.
    if datetime.now() > expires:
        return redirect

    # Even with a valid token, we force a re-auth every few hours.
    if (datetime.now() - created).total_seconds() > 60 * 60 * FORCE_REAUTH:
        return redirect

    # Set a new cookie with a new expire time.
    payload["expires"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    response = flask.make_response(flask.jsonify(payload))
    response.set_cookie(COOKIE, jwt.encode(payload, SECRET))

    return response


if __name__ == "__main__":
    app.secret_key = "secret"
    app.run(debug=True, port=5001)
