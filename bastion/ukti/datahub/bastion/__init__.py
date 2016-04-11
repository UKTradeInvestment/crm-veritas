import os
import random
import string

from dotenv import load_dotenv

from ukti.datahub.bastion.app import app, BadRequestException
from ukti.datahub.bastion.views import BastionView

__version__ = (0, 0, 1)

# Tap the environment file if it's available
if os.path.exists("/etc/veritas.conf"):
    load_dotenv("/etc/veritas.conf")

if __name__ == "__main__":

    app.secret_key = ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(64))

    app.add_url_rule('/', defaults={"path": ""},
                     view_func=BastionView.as_view("BastionRoot"))
    app.add_url_rule('/<path:path>',
                     view_func=BastionView.as_view("BastionView"))

    app.run(debug=True, port=5001)
