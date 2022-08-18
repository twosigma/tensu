# TENSU
Tensu is a TUI (curses) based program for interacting with SensuGo Enterprises' monitoring pipeline and backend API. It aims to be a powerful tool for Infrastructure Engineers and System Administrators to interact with their monitoring and alerting infrastructure without leaving the comfort of their terminal.

![screenshot](/misc/screenshot-1.jpg "Screenshot")
![screenshot](/misc/screenshot-2.jpg "Screenshot")

# Installation

Requirements:

* Python 3.7+

```
pip3 install -r requirements.txt
```

### Known installation issues
If you are experiencing trouble when installing gssapi python, ensure you install the `libkrb5-dev` package (Debian/Ubuntu) or `krb5-devel` (Redhat/CentoS/Fedora)

# First run
```
tensu.py --configure-api-url https://my-sensu-backend.com:8080/
```

# First run, specify SSL trust anchors
```
tensu.py --configure-api-url https://my-sensu-backend.com:8080/ --verify-cert-bundle /path/to/ssl/certs.crt
```

# Authentication
Tensu will do a best effort determination to pick the correct authentication method:

* If `-k` is specified on the command line, it will read a SENSU API KEY from a flat file and use that for API Key authentication.
* If an environment variable `SENSU_API_KEY` exists, it will use that for API Key authentication.
* If an environment variable `KRB5CCNAME` exists, it will use that for Kerberos authentication.
* If none of the above options are found, it will default to BASIC AUTHENTICATION (username and password combination) and will prompt in the app.
* When using KERBEROS or BASIC authentication, a JWT and refresh token is fetched and persisted in the app's configuration file.
* When using `-k` the API Key will persisted in the app's configuration file.

# Application configuration state
Application configuration state is persisted to `$HOME/.config/tensu/state` in JSON format.


