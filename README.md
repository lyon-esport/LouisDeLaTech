LouisDeLaTech is a discord bot manager for Lyon e-Sport

![Python test](https://github.com/lyon-esport/intranet/workflows/Python%20test/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Requirements
- Python (check version in setup.py)

# Setup
## Discord
Create a [discord bot](https://discord.com/developers/applications) and get the token

## Google
- Create a [google project](https://console.cloud.google.com/iam-admin)
- Create a [google service account](https://console.cloud.google.com/iam-admin/serviceaccounts)
- Enable Google workspace delegation
- Generate keys and download the file (used by the bot `-g`)
- [Add required scopes](https://admin.google.com/ac/owl/domainwidedelegation) for the service account (see config.example for the list of scopes)

# Install
## Install dependencies
### Production

    $ pip install -e .[production]

### Dev

    $ pip install -e .[dev]
    $ pre-commit install

## Configure

Fill `config.toml` with `config.example`

## Run

    $ python main.py -c config.toml -g google.json

# Licence

The code is under CeCILL license.

You can find all details here: https://cecill.info/licences/Licence_CeCILL_V2.1-en.html

# Credits

Copyright © Lyon e-Sport, 2021

Contributor(s):

-Ortega Ludovic - ludovic.ortega@lyon-esport.fr
