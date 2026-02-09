# Changelog
All notable changes to this project are documented here.

## [Unreleased] - 2026-01-30
### Added
- More explicit log format (timestamp + level + logger + line). (`src/les_louisdelatech/main.py`)
- Validation for OTP digest/digits. (`src/les_louisdelatech/extensions/otp.py`)
- Developer documentation in `docs/` and explanatory docstrings/comments across the codebase.

### Fixed
- HelloAsso pagination (no more infinite loop). (`src/les_louisdelatech/utils/hello_asso.py`)
- HelloAsso access token header (Bearer uses access_token). (`src/les_louisdelatech/bot.py`)
- `ctx.send` calls properly awaited in HelloAsso commands. (`src/les_louisdelatech/extensions/hello_asso.py`)
- OTP “not found” now handled cleanly. (`src/les_louisdelatech/extensions/otp.py`)
- Discord voice channel creation now handles missing category. (`src/les_louisdelatech/extensions/management.py`)
- Bot presence task now handles empty activity list. (`src/les_louisdelatech/extensions/task.py`)
- Google API error formatting more robust. (`src/les_louisdelatech/utils/gsuite.py`)
- GSuite user creation avoids sending `None` fields. (`src/les_louisdelatech/utils/gsuite.py`)
- Bot sync flag and close lifecycle fixed. (`src/les_louisdelatech/bot.py`)

### Step-by-step update (devs)
1) `git pull` on `main`.
2) Restart the bot so the new logging format takes effect.
3) (If OTP is used) verify allowed digests: `sha1`, `sha256`, `sha512`.
4) (If HelloAsso is used) run `/ha_check_update` on a form slug to confirm pagination works.

## [2026-01-30] - Credential delivery update
### Changed
- Credentials are now sent by email (not Discord DM). (`src/les_louisdelatech/extensions/user.py`)
- Password generation uses only alphanumeric characters (copy/paste safe). (`src/les_louisdelatech/utils/password.py`)
- Added Gmail send helper. (`src/les_louisdelatech/utils/email.py`)

### Step-by-step update (devs)
1) Add Gmail send scope in config:
   - `https://www.googleapis.com/auth/gmail.send`
2) Ensure `google.subject` is set (sender address).
3) Restart the bot.
4) Test `/provision` and `/rpassword` with a test user.
