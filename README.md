# Veritas

An auth server for the CRM replacement service.


## Setup

We're using the super-handy [dotenv](https://github.com/theskumar/python-dotenv)
library, so setting up can either be done by setting environment
variables the old fashioned way or by placing the required values into
`/etc/veritas.conf`:

    VERITAS_BASTION_SECRET="this is a secret"
    VERITAS_AUTH_SECRET="this is a different secret"
    VERITAS_CLIENT_ID="<comes from Azure>"
    VERITAS_CLIENT_SECRET="<comes from Azure>"
    VERITAS_APP_TOKEN="<comes from Azure>"


## Running

There are three components here, but only one should be considered the
the actual Veritas server:

* `data.py`: A sample of the auth code required to run on the data
  layer.  This machine is not meant to be public-facing.
* `bastion.py`: A sample of the auth code required to run on the bastion
  layer.  This service *is* publicly facing and serves as relay layer
  for security between the public and the data server.
* `veritas.py`: The actual veritas server.

In each instance, you can start these services by invoking Python
against the file:

    $ python data.py
    $ python bastion.py
    $ python veritas.py


## Colophon

From [Wikipedia](https://en.wikipedia.org/wiki/Veritas):

> In Roman mythology, Veritas, meaning truth, was the goddess of truth,
> a daughter of Saturn and the mother of Virtue. It was believed that
> she hid in the bottom of a holy well because she was so elusive. Her
> image is shown as a young virgin dressed in white.
