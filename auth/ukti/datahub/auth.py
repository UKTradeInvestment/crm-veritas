import flask
import random
import string
import os
import uuid

from dotenv import load_dotenv

from ukti.datahub.veritas import Veritas

# Tap the environment file if it's available
if os.path.exists("/etc/veritas.conf"):
    load_dotenv("/etc/veritas.conf")

__version__ = (0, 0, 1)

app = flask.Flask(__name__)
app.secret_key = ''.join(
    random.choice(string.ascii_letters + string.digits) for _ in range(64))


@app.route('/')
def index():
    """
    All UI frontends need to do two simple things:

    * Check if the user has a cookie, and if not:
    * Bounce them to this auth server at "/".
    """

    veritas = Veritas.build(os.environ)

    if "next" not in flask.request.args:
        return flask.abort(
            400, description="You must specify a next= parameter.")

    if flask.request.cookies.get(veritas.COOKIE):
        if "next" in flask.session:
            return flask.redirect(flask.session["next"])

    flask.session["next"] = flask.request.args["next"]
    flask.session["state"] = str(uuid.uuid4())

    url = veritas.get_auth_url(flask.session["state"])

    return flask.redirect(url)


@app.route('/oauth2')
def oauth2():
    """
    This is where Azure drops the user after it's done with them.
    """

    veritas = Veritas.build(os.environ)

    if "code" not in flask.request.args:
        return flask.redirect("/")

    if "state" not in flask.request.args:
        return flask.abort(403)

    if "state" not in flask.session:
        return flask.abort(403)

    if not flask.request.args["state"] == flask.session["state"]:
        return flask.abort(403)

    response = flask.redirect(flask.session["next"])
    response.set_cookie(
        veritas.COOKIE, veritas.get_auth_cookie(flask.request.args["code"]))

    return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)
