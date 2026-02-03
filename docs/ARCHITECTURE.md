# Architecture

This document explains how LouisDeLaTech works at a high level, and where to
start when you need to debug or extend it.

## What the bot does

- Provision users:
  - Create Google Workspace accounts (@lyon-esport.fr)
  - Add users to Google Groups (per team)
  - Configure Gmail signature
  - Apply Discord roles and nickname
  - Send credentials by email (not Discord DM)
- Validate memberships via HelloAsso (paid vs unpaid, new vs update)
- Manage OTP secrets per team (encrypted secrets in SQLite)
- Small Discord management utilities (topic, auto meeting voice channels)

## Entry point

- `src/les_louisdelatech/main.py`
  - Loads `config.toml`
  - Configures logging
  - Starts the bot with the Discord token

## Core bot wiring

- `src/les_louisdelatech/bot.py`
  - Loads extensions/cogs from `discord.initial_cogs`
  - Initializes SQLite with Tortoise ORM
  - Exposes:
    - `admin_sdk()` for Google Admin SDK (domain-wide delegation)
    - `gmail_sdk(user)` for Gmail Settings API (delegated as user)
    - `mailer_sdk()` for sending emails (delegated as `google.subject`)
  - Manages HelloAsso OAuth2 token lifecycle
  - Provides `encrypt/decrypt` (Fernet) for OTP secrets

## Extensions (cogs)

All user-facing behavior lives in `src/les_louisdelatech/extensions/`.

- `user.py`
  - `/provision`: create user across Google + Discord and send credentials by email
  - `/deprovision`: suspend Google user and remove Discord roles
  - `/uteam`: move user to another team (Google + Discord + signature)
  - `/usignatures`: bulk update signatures
  - `/rpassword`: reset password and email temporary password
- `hello_asso.py`
  - `/ha_check_update`: diff HelloAsso paid members vs Google users
  - `/ha_verify_payment`: list Google users without paid HelloAsso membership
- `otp.py`
  - `/lotp`, `/gotp`, `/cotp`, `/dotp`
- `management.py`
  - `/topic`
  - auto-create/delete meeting voice channels
- `task.py`
  - rotates the bot presence periodically
- `config.py`, `cats.py`
  - small helper commands

## Utilities

- `src/les_louisdelatech/utils/gsuite.py`
  - thin wrappers around Google APIs (Admin SDK + Gmail Settings)
- `src/les_louisdelatech/utils/hello_asso.py`
  - fetches paginated orders from HelloAsso
- `src/les_louisdelatech/utils/email.py`
  - sends emails via Gmail API using raw RFC 2822 messages
- `src/les_louisdelatech/utils/User.py`
  - maps identity fields between HelloAsso / Google / Discord

## Data model

- SQLite database (default `db.sqlite3`)
  - Only used for OTP entries (`models/otp.py`)
  - OTP secrets are stored encrypted with Fernet

## Configuration map (quick)

- `discord.token`: bot token
- `discord.initial_cogs`: list of extensions to load
- `teams.<team_key>`:
  - `discord`: Discord role name for the team
  - `google_email`: Google Group email for the team
  - `message_template`: file name in `templates/discord/`
  - `team_role`: whether the team should appear in the signature
- `google.subject`: delegated mailbox used for Admin SDK and for sending emails
- `google.scopes.admin`: Admin SDK scopes
- `google.scopes.gmail`: Gmail scopes (needs `gmail.send` to send credentials)
- `hello_asso.*`: OAuth2 client credentials + org slug
- `db.secret_key`: Fernet key (used to encrypt OTP secrets)

## Where to start debugging

- Start up issues:
  - Check logs from `main.py` (log level and config load)
  - Validate `config.toml` keys match `config.example`
- Provisioning issues:
  - `extensions/user.py` + `utils/gsuite.py`
- HelloAsso issues:
  - `bot.py` (token) + `utils/hello_asso.py` (pagination) + `extensions/hello_asso.py`
- OTP issues:
  - `extensions/otp.py` + `models/otp.py` + `bot.encrypt/decrypt`

