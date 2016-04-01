# Bastion server example

import flask
import jwt
import os
import requests

from dotenv import load_dotenv

from common import AUTH_SERVER, COOKIE, DATA_SERVER, HEADER_NAME

# Tap the environment file if it's available
if os.path.exists(".env"):
    load_dotenv(".env")

SECRET = os.getenv("BASTION_SECRET")


app = flask.Flask(__name__)


@app.route("/")
def index():

    # No cookie? Come back when you have one.
    # Strictly speaking, this should never happen because the UI should be
    # smart enough not to hit up the bastion server without a cookie.
    if COOKIE not in flask.request.cookies:
        return flask.abort(400, description=requests.Request(
            "GET",
            AUTH_SERVER,
            params={
                "next": flask.redirect(flask.request.environ["HTTP_REFERER"])
            }
        ).prepare().url)

    # Relay the request to the data server and create a response for the client
    # with whatever we got.  We don't do any processing of the relayed request
    # here because the bastion host doesn't have the means to verify the auth
    # server's jwt.
    data_response = requests.get(
        "{}/arbitrary-endpoint".format(DATA_SERVER),
        params=flask.request.args,
        headers={
            HEADER_NAME: jwt.encode(
                {"token": flask.request.cookies[COOKIE]},
                SECRET
            )
        }
    )

    if data_response.status_code >= 300:
        return flask.abort(data_response.status_code, data_response.text)

    response = flask.make_response(data_response.text)

    # Set a new cookie based on the auth token found inside the response from
    # the data server.
    response.set_cookie(
        COOKIE,
        jwt.decode(data_response.headers[HEADER_NAME], SECRET)["session"]
    )

    return response


if __name__ == "__main__":
    app.secret_key = "secret"
    app.run(debug=True, port=5001)
