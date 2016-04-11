import flask
import jwt
import os

from flask.views import View

from ukti.datahub.veritas import Veritas
from ukti.datahub.bastion.app import BadRequestException


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
            raise BadRequestException(self.veritas.get_bastion_redirect_url(
                flask.request.path
            ))

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
