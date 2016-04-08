import flask
import jwt
import os
import random
import string

from dotenv import load_dotenv
from flask.views import View

from ukti.datahub.veritas import Veritas

__version__ = (0, 0, 1)

# Tap the environment file if it's available
if os.path.exists("/etc/veritas.conf"):
    load_dotenv("/etc/veritas.conf")

app = flask.Flask(__name__)


class BastionView(View):

    methods = ["GET"]

    def __init__(self):
        View.__init__(self)
        self.veritas = Veritas(
            bastion_server=os.getenv("BASTION_SERVER"),
            bastion_secret=os.getenv("BASTION_SECRET")
        )

    def dispatch_request(self, *args, **kwargs):

        # No cookie? Come back when you have one.
        if self.veritas.COOKIE not in flask.request.cookies:
            return flask.abort(
                400,
                description=self.veritas.get_bastion_redirect_url(
                    flask.request.path
                )
            )

        # Relay the request to the data server and create a response for the
        # client with whatever we got.  We don't do any processing of the
        # relayed request here because the bastion host doesn't have the means
        # to verify the auth server's jwt.
        data_response = self.veritas.get_data_response(
            flask.request.path,
            flask.request.args,
            flask.request.cookies[self.veritas.COOKIE]
        )

        if data_response.status_code >= 300:
            return flask.abort(data_response.status_code, data_response.text)

        response = flask.make_response(
            data_response.text,
            data_response.status_code
        )

        # There's an auth token in the data server's response header, so we set
        # it as a new cookie.
        response.set_cookie(
            self.veritas.COOKIE,
            jwt.decode(
                data_response.headers[self.veritas.HEADER_NAME],
                self.veritas.bastion_secret
            )[self.veritas.SESSION]
        )

        return response


app.add_url_rule(
    '/', defaults={"path": ""}, view_func=BastionView.as_view("BastionRoot"))
app.add_url_rule('/<path:path>', view_func=BastionView.as_view("BastionView"))

if __name__ == "__main__":
    app.secret_key = ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(64))
    app.run(debug=True, port=5001)
