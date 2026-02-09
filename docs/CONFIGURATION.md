# Configuration

LouisDeLaTech is configured via a TOML file (based on `config.example`).

## Files

- `config.toml`: main config (tokens, team mapping, scopes, etc.)
- `google.json`: Google service account key used for domain-wide delegation
- `db.sqlite3`: SQLite database for OTP storage (created at runtime)

## Minimal required config

### Discord

- `discord.token`: the Discord bot token
- `discord.command_prefix`: optional legacy prefix
- `discord.initial_cogs`: which features are enabled

### Google

- `google.subject`: mailbox used for delegation (sender + admin actions)
- `google.scopes.admin`: Admin SDK scopes
- `google.scopes.gmail`: Gmail scopes
  - must include `https://www.googleapis.com/auth/gmail.send` to send credentials

### Database (OTP)

- `db.filename`: SQLite file path
- `db.secret_key`: Fernet key used to encrypt OTP secrets

### HelloAsso (optional)

- `hello_asso.organization`: org slug
- `hello_asso.client_id` / `hello_asso.client_secret`

## Notes

- The Google Admin schema must contain `custom.discordId` (see README).
- If you disable a cog (remove from `discord.initial_cogs`), its commands and
  listeners will not be available.

