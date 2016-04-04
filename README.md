# Veritas

An auth server for the CRM replacement service.


## Request Path

![Diagram of the Authentication Path](auth-path.png)

1. UI server attempts a request to the bastion server.
2. The bastion server rejects the request (400) with a message to visit
   the auth server for authorisation.
3. The UI redirects the user to the auth server at `/`.
4. The auth server, noting that the user doesn't yet have a cookie,
   bounces them to Azure for Microsoft's authorisation gymnastics.
5. Azure bounces the user back to the auth server along with a `code=`
   parameter, which we then bundle into a JSON web token using the
   auth server's secret.
6. We stuff that jwt into a cookie and return the user to the UI.
7. The UI makes another request to the bastion server.  This time with
   the cookie, so it succeeds.
8. The bastion server creates another jwt using its own secret and
   stuffs the auth server jwt into it.  It includes this in a header
   when it relays the request to the data server.
9. The data server receives the nested jwts and verifies both, then uses
   the auth code in there to request user data from Azure.
10. Azure responds with a bunch of user data in another jwt which the
   data server then dumps into a local data store.
11. The data server responds with the data requested and a new session
   id to be passed up the chain.
12. The bastion server passes on this session id to the UI, where it can
   be used for future requests, bypassing the auth gymnastics.


## Setup

We're using the super-handy [dotenv](https://github.com/theskumar/python-dotenv)
library, so setting up can either be done by setting environment
variables the old fashioned way or by placing the required values into
a filed called `.env`:

    AUTH_SERVER="http://localhost:5000"
    BASTION_SERVER="http://localhost:5001"
    DATA_SERVER="http://localhost:5002"

    AUTH_SECRET="this is a different secret"
    BASTION_SECRET="this is a secret"
    CLIENT_ID="<comes from Azure>"
    CLIENT_SECRET="<comes from Azure>"
    APP_TOKEN="<comes from Azure>"


## Running

There are three components here, but only one should be considered the
the actual Veritas server:

* `auth.py`: The actual auth server.
* `bastion.py`: A sample of the auth code required to run on the bastion
  layer.  This service *is* publicly facing and serves as relay layer
  for security between the public and the data server.
* `data.py`: A sample of the auth code required to run on the data
  layer.  This machine is not meant to be public-facing.

In each instance, you can start these services by invoking Python
against the file:

    $ python auth.py
    $ python bastion.py
    $ python data.py


## Colophon

From [Wikipedia](https://en.wikipedia.org/wiki/Veritas):

> In Roman mythology, Veritas, meaning truth, was the goddess of truth,
> a daughter of Saturn and the mother of Virtue. It was believed that
> she hid in the bottom of a holy well because she was so elusive. Her
> image is shown as a young virgin dressed in white.
