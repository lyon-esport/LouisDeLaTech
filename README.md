# LouisDeLaTech is a discord bot manager for Lyon e-Sport

[![PyPI](https://img.shields.io/pypi/v/les-louisdelatech.svg)](https://pypi.python.org/pypi/les-louisdelatech)
[![PyPI versions](https://img.shields.io/pypi/pyversions/les-louisdelatech.svg)](https://pypi.python.org/pypi/les-louisdelatech)
[![Python test](https://github.com/lyon-esport/LouisDeLaTech/actions/workflows/test.yml/badge.svg)](https://github.com/lyon-esport/LouisDeLaTech/actions/workflows/test.yml)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Requirements

- Python (check version in setup.py)

## Setup

### Discord

Create a [discord bot](https://discord.com/developers/applications) and get the token

### Google

- Create a [google project](https://console.cloud.google.com/iam-admin)
- Create a [google service account](https://console.cloud.google.com/iam-admin/serviceaccounts)
- Enable Google workspace delegation
- Generate keys and download the file (used by the bot `-g`)
- [Add required scopes](https://admin.google.com/ac/owl/domainwidedelegation) for the service account (see config.example for the list of scopes)

You must create [user custom attribute](https://admin.google.com/ac/customschema?hl=fr)

```json
custom: {
 pseudo: ""
 discordId: ""
}
```

# Install

```bash
pip install les_louisdelatech
```

# Configure

Generate a secret_key to encrypt database secrets

```python
>>> from cryptography.fernet import Fernet
>>> Fernet.generate_key()
```

Fill `config.toml` with `config.example`

# Run

```bash
python3 -m les_louisdelatech.main -c config.toml -g google.json
```

# Dev

Install [Poetry](https://python-poetry.org/docs/master/#installing-with-the-official-installer) with version >= 1.2.0a1

```bash
poetry install
poetry shell
pre-commit install
```

### Run pre-commit
```
pre-commit run --all-files
```

## Licence

The code is under CeCILL license.

You can find all details here: <https://cecill.info/licences/Licence_CeCILL_V2.1-en.html>

## Credits

Copyright © Lyon e-Sport, 2021

Contributor(s):

- Ortega Ludovic - ludovic.ortega@lyon-esport.fr
- Etienne "PoPs" G. - etienne.guilluy@lyon-esport.fr
- Pierre "DrumSlayer" Sarret - pierre.sarret@lyon-esport.fr
