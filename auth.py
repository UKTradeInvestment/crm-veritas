import flask
import jwt
import os
import requests
import uuid

from dotenv import load_dotenv

from common import COOKIE, AUTH_SERVER, AZURE

# Tap the environment file if it's available
if os.path.exists(".env"):
    load_dotenv(".env")

SECRET = os.getenv("AUTH_SECRET")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

REDIRECT_URI = "{}/oauth2".format(AUTH_SERVER)

AZURE_AUTHORISE = "{}/common/oauth2/authorize".format(AZURE)

app = flask.Flask(__name__)


@app.route('/')
def index():

    next_error = "You must specify a next= parameter."

    # if flask.request.cookies.get(COOKIE):
    #     if "next" in flask.session:
    #         return flask.redirect(flask.session["next"])
    #     if "HTTP_REFERER" in flask.request.environ:
    #         return flask.redirect(flask.request.environ["HTTP_REFERER"])
    #     return flask.abort(400, description=next_error)

    if "next" not in flask.request.args:
        return flask.abort(400, description=next_error)

    flask.session["next"] = flask.request.args["next"]
    flask.session["state"] = str(uuid.uuid4())

    return flask.redirect(requests.Request(
        "GET",
        AZURE_AUTHORISE,
        params={
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "state": flask.session["state"]
        }
    ).prepare().url)


@app.route('/oauth2')
def oauth2():
    """
    This is where Azure drops the user after it's done with them.
    """

    if "code" not in flask.request.args:
        return flask.redirect("/")

    if "state" not in flask.request.args:
        return flask.abort(403)

    if not flask.request.args["state"] == flask.session["state"]:
        return flask.abort(403)

    response = flask.redirect(flask.session["next"])
    response.set_cookie(
        COOKIE, jwt.encode({
            "code": flask.request.args["code"],
            "nonce": str(uuid.uuid4())
        }, SECRET))

    return response


if __name__ == '__main__':
    app.secret_key = "secret"
    app.run(debug=True, port=5000)
