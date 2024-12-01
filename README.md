# LouisDeLaTech is a discord bot manager for Lyon e-Sport

[![PyPI](https://img.shields.io/pypi/v/les-louisdelatech.svg)](https://pypi.python.org/pypi/les-louisdelatech)
[![PyPI versions](https://img.shields.io/pypi/pyversions/les-louisdelatech.svg)](https://pypi.python.org/pypi/les-louisdelatech)
[![Python test](https://github.com/lyon-esport/LouisDeLaTech/actions/workflows/test.yml/badge.svg)](https://github.com/lyon-esport/LouisDeLaTech/actions/workflows/test.yml)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

# Setup

## Discord

Create a [discord bot](https://discord.com/developers/applications) and get the token

## Google

- Create a [google project](https://console.cloud.google.com/iam-admin)
- Create a [google service account](https://console.cloud.google.com/iam-admin/serviceaccounts)
- Enable Google workspace delegation
- Generate keys and download the file (used by the bot `-g`)
- [Add required scopes](https://admin.google.com/ac/owl/domainwidedelegation) for the service account (see config.example for the list of scopes)

You must create [user custom attribute](https://admin.google.com/ac/customschema?hl=fr)

```json
"custom": {
 "pseudo": "",
 "discordId": "",
 "teeShirt": "",
 "birthdate": ""
}
```

## HelloAsso
[Documentation](https://centredaide.helloasso.com/s/article/api-comment-fonctionne-l-api-helloasso)

Custom fields (Actually hard-coded)
```json
{
    "name": "Pseudonyme",
    "type": "TextInput",
},
{
    "name": "Date de naissance",
    "type": "Date",
},
{
    "name": "Adresse postale",
    "type": "TextInput",
},
{
    "name": "Numéro de téléphone",
    "type": "TextInput",
},
{
    "name": "Nom d'utilisateur Discord",
    "type": "TextInput",
},
{
    "name": "Taille du tee-shirt",
    "type": "ChoiceList",
},
{
    "name": "Je m'engage à signer l'engagement de confidentialité : https://example.fr",
    "type": "YesNo",
}
```
To use the commands, please provide the requested form slug. \
For exemple, for form at `helloasso.com/associations/masuperassociation/adhesions/adhesion-2024-2025/` , the slug is `adhesion-2024-2025`  \
Resulting in, for exemple, the following command : `/ha_check_update form_slug:adhesion-2024-2025`
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
Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

Install and setup dependencies with `uv sync --all-extras`

## Run ruff
```
uv run ruff format . 
uv run ruff check .
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
