# LouisDeLaTech is a discord bot manager for Lyon e-Sport

![Python test](https://github.com/lyon-esport/LouisDeLaTech/workflows/Python%20test/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

## Install

### Install dependencies

#### Production

```bash
pip install -e .
```

#### Dev

```bash
pip install -e .[dev]
pre-commit install
```

### Configure

Generate a secret_key to encrypt database secrets

```python
>>> from cryptography.fernet import Fernet
>>> Fernet.generate_key()
```

Fill `config.toml` with `config.example`

### Run

```bash
python main.py -c config.toml -g google.json
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
