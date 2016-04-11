import flask
import random
import string

from ukti.datahub.bastion.exceptions import BadRequestException
from ukti.datahub.bastion.views import BastionView

__version__ = (0, 0, 1)

app = flask.Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False


#
# Error handlers
#


@app.errorhandler(BadRequestException)
def handle_invalid_usage(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


#
# Routers
#


app.add_url_rule('/', defaults={"path": ""},
                 view_func=BastionView.as_view("BastionRoot"))
app.add_url_rule('/<path:path>',
                 view_func=BastionView.as_view("BastionView"))


if __name__ == "__main__":
    app.secret_key = ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(64))
    app.run(debug=True, port=5001)
