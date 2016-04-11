import flask

app = flask.Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False


class BadRequestException(Exception):

    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        r = dict(self.payload or ())
        r["message"] = self.message
        return r


@app.errorhandler(BadRequestException)
def handle_invalid_usage(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
