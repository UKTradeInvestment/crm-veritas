# Bastion server example

import flask
import jwt
import os

from dotenv import load_dotenv

from veritas import Veritas

# Tap the environment file if it's available
if os.path.exists(".env"):
    load_dotenv(".env")

app = flask.Flask(__name__)
veritas = Veritas(
    bastion_server=os.getenv("BASTION_SERVER"),
    bastion_secret=os.getenv("BASTION_SECRET")
)


@app.route("/")
def index():

    # No cookie? Come back when you have one.
    if veritas.COOKIE not in flask.request.cookies:
        return flask.abort(
            400, description=veritas.get_bastion_redirect_url("/"))

    # Relay the request to the data server and create a response for the client
    # with whatever we got.  We don't do any processing of the relayed request
    # here because the bastion host doesn't have the means to verify the auth
    # server's jwt.
    data_response = veritas.get_data_response(
        "/arbitrary-endpoint",
        flask.request.args,
        flask.request.cookies[veritas.COOKIE]
    )

    if data_response.status_code >= 300:
        return flask.abort(data_response.status_code, data_response.text)

    response = flask.make_response(
        data_response.text,
        data_response.status_code
    )

    # There's an auth token in the data server's response header, so we set it
    # as a new cookie.
    response.set_cookie(
        veritas.COOKIE,
        jwt.decode(
            data_response.headers[veritas.HEADER_NAME],
            veritas.bastion_secret
        )["session"]
    )

    return response


if __name__ == "__main__":
    app.secret_key = "secret"
    app.run(debug=True, port=5001)
