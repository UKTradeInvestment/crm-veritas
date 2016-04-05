import flask
import uuid

from veritas import Veritas


app = flask.Flask(__name__)
veritas = Veritas()


@app.route('/')
def index():
    """
    All UI frontends need to do two simple things:

    * Check if the user has a cookie, and if not:
    * Bounce them to this auth server at "/".
    """

    if "next" not in flask.request.args:
        return flask.abort(
            400, description="You must specify a next= parameter.")

    if flask.request.cookies.get(veritas.COOKIE):
        return flask.redirect(flask.session["next"])

    flask.session["next"] = flask.request.args["next"]
    flask.session["state"] = str(uuid.uuid4())

    url = veritas.get_auth_url(flask.session["state"])
    print("Redirecting: {}".format(url))
    return flask.redirect(url)


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
    veritas.set_auth_cookie(response, flask.request.args["code"])

    return response


if __name__ == '__main__':
    app.secret_key = veritas.AUTH_SECRET
    app.run(debug=True, port=5000)
