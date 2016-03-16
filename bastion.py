# Bastion server example

import flask
import jwt
import os
import requests

from urllib.parse import quote as url_encode

from common import (
    AUTH_SERVER, BASTION_SERVER, COOKIE, DATA_SERVER, HEADER_NAME)

SECRET = os.getenv("VERITAS_BASTION_SECRET")


app = flask.Flask(__name__)


@app.route("/")
def index():

    # We attach `next=` to the redirect so that the auth server knows where it
    # should bounce the user back when everything is finished.
    redirect = flask.redirect("{}?next={}".format(
        AUTH_SERVER,
        url_encode(BASTION_SERVER)
    ))

    # No cookie? > Go get one.
    if COOKIE not in flask.request.cookies:
        return redirect

    # Relay the request to the data server and create a response for the client
    # with whatever we got.
    data_response = requests.get("{}endpoint".format(DATA_SERVER))
    response = flask.make_response(flask.jsonify(data_response.json()))

    # Set a new cookie based on the auth token found inside the response from
    # the data server.
    response.set_cookie(
        COOKIE,
        jwt.decode(data_response.headers[HEADER_NAME], SECRET)["token"]
    )

    return response


if __name__ == "__main__":
    app.secret_key = "secret"
    app.run(debug=True, port=5001)
