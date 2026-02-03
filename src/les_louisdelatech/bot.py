import logging
import os
import sys
import traceback

import discord
from cryptography.fernet import Fernet
from discord.ext import commands
from google.oauth2.service_account import Credentials
from googleapiclient import discovery
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from tortoise import Tortoise, connections

logger = logging.getLogger()

"""
Core Discord bot implementation.

This file defines the `LouisDeLaTech` bot class which:
- Loads Discord extensions ("cogs") configured in `config.toml`
- Initializes the SQLite database (Tortoise ORM) used for OTP secrets
- Exposes helpers for Google Admin SDK / Gmail SDK using domain-wide delegation
- Manages HelloAsso OAuth2 token acquisition/refresh

High-level startup flow:
1) `main.py` loads the config and instantiates `LouisDeLaTech`
2) Discord calls `setup_hook()` once at startup to load extensions and init DB
3) The bot reacts to commands/events via extensions in `src/les_louisdelatech/extensions`
"""


class LouisDeLaTech(commands.Bot):
    def __init__(self, config, google_path):
        super().__init__(
            command_prefix=config["discord"]["command_prefix"],
            description="LouisDeLaTech is a discord bot manager for Lyon e-Sport",
            intents=discord.Intents(
                messages=True,
                message_content=True,
                guilds=True,
                voice_states=True,
                members=True,
            ),
        )
        # added to make sure that the command tree will be synced only once
        self.synced = False

        self.root_dir = os.path.dirname(os.path.abspath(__file__))

        self.config = config
        self.google_path = google_path

        self.fernet = Fernet(self.config["db"]["secret_key"])

        self.hello_asso = self.setup_hello_asso_client()
        self._hello_asso_fetch_token()

    def setup_hello_asso_client(self):
        """Build an OAuth2 client for HelloAsso.

        HelloAsso uses OAuth2 client credentials. `requests-oauthlib` handles
        refreshing and token management.
        """
        client = BackendApplicationClient(
            client_id=self.config["hello_asso"]["client_id"]
        )
        oauth = OAuth2Session(
            client=client,
            auto_refresh_url="https://api.helloasso.com/oauth2/token",
            auto_refresh_kwargs={
                "client_id": self.config["hello_asso"]["client_id"],
                "client_secret": self.config["hello_asso"]["client_secret"],
            },
            token_updater=self._hello_asso_token_saver,
        )

        return oauth

    def _hello_asso_fetch_token(self):
        """Fetch an initial HelloAsso access token at startup."""
        result = self.hello_asso.fetch_token(
            token_url=self.hello_asso.auto_refresh_url,
            auth=HTTPBasicAuth(
                self.config["hello_asso"]["client_id"],
                self.config["hello_asso"]["client_secret"],
            ),
        )
        self._hello_asso_token_saver(result)

    def _hello_asso_token_saver(self, token: str):
        """Store token in session and keep Authorization header in sync.

        `fetch_token()` returns a dict, but `OAuth2Session` will call token_updater
        with the token dict as well. We normalize to an `access_token` string.
        """
        access_token = token
        if isinstance(token, dict):
            access_token = token.get("access_token")
            self.hello_asso.token = token
        if not access_token:
            logger.error("HelloAsso token missing access_token")
            return
        self.hello_asso.headers = {"authorization": f"Bearer {access_token}"}

    def get_entity_to_skip(self, entity: str, provider: str):
        """Get configured entities to skip (e.g. teams not managed by the bot).

        Config shape:
        [to_skip]
          [[to_skip.teams]]
          discord = "Alumnis"
          google = "alumnis"
        """
        teams = []

        for entity in self.config["to_skip"][entity]:
            if provider in entity:
                teams.append(entity[provider])

        return teams

    def encrypt(self, s: str):
        """Encrypt a secret for storage (OTP secrets)."""
        return self.fernet.encrypt(s.encode("ascii"))

    def decrypt(self, s: str):
        """Decrypt a stored secret (OTP secrets)."""
        return self.fernet.decrypt(s).decode("ascii")

    async def setup_hook(self):
        """Discord.py startup hook.

        Called once by discord.py after login and before the bot becomes ready.
        We use it to:
        - load extensions/cogs
        - initialize the SQLite DB schema for OTPs
        """
        for extension in self.config["discord"]["initial_cogs"]:
            await self.load_extension(extension)

        await Tortoise.init(
            db_url=f"sqlite://{self.config['db']['filename']}",
            modules={"models": ["les_louisdelatech.models"]},
        )
        await Tortoise.generate_schemas()

    def admin_sdk(self):
        """Build a Google Admin SDK client using domain-wide delegation."""
        creds = Credentials.from_service_account_file(
            self.google_path,
            scopes=self.config["google"]["scopes"]["admin"],
            subject=self.config["google"]["subject"],
        )

        return discovery.build(
            "admin", "directory_v1", credentials=creds, cache_discovery=False
        )

    def gmail_sdk(self, user: str):
        """Build a Gmail API client delegated as `user`."""
        creds = Credentials.from_service_account_file(
            self.google_path,
            scopes=self.config["google"]["scopes"]["gmail"],
            subject=user,
        )

        return discovery.build("gmail", "v1", credentials=creds, cache_discovery=False)

    def mailer_sdk(self):
        """Gmail API client used to send emails from the delegated subject mailbox."""
        return self.gmail_sdk(self.config["google"]["subject"])

    async def on_ready(self):
        logger.info(f"Logged in as: {self.user.name} - {self.user.id}")
        logger.info("Successfully logged in and booted...!")
        if not self.synced:  # check if slash commands have been synced
            await self.tree.sync()
            self.synced = True
            logger.info("Slash commands synced")

    async def on_command_error(self, ctx, error: Exception):
        if isinstance(error, discord.ext.commands.errors.CommandNotFound):
            await ctx.send("Command not found")
        elif isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(
                f":no_entry: Error while executing command => {error.__cause__}"
            )
        else:
            await ctx.send(
                f":no_entry: Error while executing command => {error.__cause__}"
            )
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )

    async def close(self):
        await connections.close_all()
        await super().close()
