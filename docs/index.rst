.. Tensu documentation master file, created by
   sphinx-quickstart on Wed May 25 21:28:49 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Tensu's documentation!
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Installation
============
To get up and running simply install the required python dependencies.::

   pip3 install -r requirements.txt

And you should be good to go!

Known installation issues
-------------------------
If you are experiencing trouble when install gssapi python, ensure you install the ``libkrb5-dev`` package (Debian/Ubuntu) or ``krb5-devel`` (Redhat/CentOS/Fedora).


First Run
=========
To start Tensu simply run ``tensu.py`` with the ``--configure-api-url`` flag. You only need to run it with this flag one time, or whenever want to configure Tensu to use a different API backend.::

   tensu.py --configure-api-url https://my-sensu-backend.com:8080/

Specifying SSL CA certificates for request verification
=======================================================
To supply your own SSL trust anchors for requests, simply run ``tensu.py`` with the ``--verify-cert-bundle`` or ``-v`` flag.::

   tensu.py --configure-api-url https://my-sensu-backend.com:8080/ --verify-cert-bundle /path/to/ssl/ca.crt

Authentication
==============
Tensu will do a best effort determination to pick the correct authentication method. This is determined by the following factors:

1. If ``-k`` (``--key-from-file``) is specified on the command line, it will read a Sensu API Key from a flat file and use that for API Key authentication.
2. If an environment variable ``SENSU_API_KEY`` exists, it will use that for API Key authentication.
3. If an environment variable ``KRB5CCNAME`` exists, it will use that for Kerberos authentication.
4. If none of the above options are found, it will default to Basic Authentication. The application will display a prompt to enter a username and password combination.
5. When using Kerberos or Basic Authentication, a JWT (JSON Web Token) and Refresh Token are fetched and persisted in the app's configuration file.
6. When using ``-k`` (``--key-from-file``) the API Key will be persisted in the app's configuration file.

Application configuration state
===============================
Application configure state is persisted to ``$HOME/.tensu/state`` in JSON format.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
