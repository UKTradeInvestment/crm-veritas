#
# This is a sample script, so obviously key components of it can't be expected
# to be useful.
#

import flask
import os
import random
import string

from dotenv import load_dotenv

from ukti.datahub.veritas import Veritas, TokenError

# Tap the environment file if it's available
if os.path.exists("/etc/veritas.conf"):
    load_dotenv("/etc/veritas.conf")

app = flask.Flask(__name__)
app.secret_key = ''.join(
    random.choice(string.ascii_letters + string.digits) for _ in range(64))

veritas = Veritas.build(os.environ)


class TokenVerificationError(Exception):
    pass


class User(object):
    """
    This is a demo, so there's no database to speak of.  Imagine this as a
    proper ORM though, where you could conceivably do something like:

      user = Session.objects.get(key="123456789").user
    """

    def __init__(self, azure_id=None, given_name=None, family_name=None):
        """
        For some reason, Micros~1 hasn't figured out that breaking up the name
        field is a Bad Idea.
        """
        self.azure_id = azure_id
        self.given_name = given_name
        self.family_name = family_name

    @classmethod
    def get_from_session(cls, session):
        if session == "123456789":
            return cls(azure_id=3)

    @classmethod
    def create(cls, azure_id, given_name, family_name):
        """Obviously, this doesn't do anything useful."""
        return User(azure_id, given_name, family_name)


def get_mock_response():
    """
    This is just to compile a response with a session id.  Obviously for a
    proper app, this would be where most of the work goes.
    """

    return_token = veritas.generate_session_token("123456789")

    response = flask.jsonify({"this": "is", "an": "arbitrary response"})
    response.headers[veritas.HEADER_NAME] = return_token

    return response


@app.route('/arbitrary-endpoint')
def endpoint():
    """
    This is the only part of this demo that means anything.  You can ignore the
    rest as effectively stand-in code.
    """

    try:
        bastion = veritas.get_token_from_headers(flask.request.headers)
    except TokenError as e:
        return flask.abort(e.status_code, description=str(e))

    # If there's a session in the jwt and it resolves to a legit user, we can
    # safely assume that the user is authenticated
    user = User.get_from_session(bastion.get(veritas.SESSION))
    if user:
        return get_mock_response()

    # There's no session in the bastion jwt, so we go looking for a token for
    # the last bits of Azure authentication

    try:
        identity = veritas.get_identity_from_nested_token(bastion)
    except TokenError as e:
        return flask.abort(e.status_code, description=str(e))

    User.create(
        identity["oid"],
        identity["given_name"],
        identity["family_name"]
    )

    return get_mock_response()


if __name__ == '__main__':
    app.run(debug=bool(os.getenv("DEBUG", "").lower() == "true"), port=5002)
