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
        result = self.hello_asso.fetch_token(
            token_url=self.hello_asso.auto_refresh_url,
            auth=HTTPBasicAuth(
                self.config["hello_asso"]["client_id"],
                self.config["hello_asso"]["client_secret"],
            ),
        )
        self._hello_asso_token_saver(result)

    def _hello_asso_token_saver(self, token: str):
        self.hello_asso.headers = {"authorization": f"Bearer {token}"}

    def get_entity_to_skip(self, entity: str, provider: str):
        teams = []

        for entity in self.config["to_skip"][entity]:
            if provider in entity:
                teams.append(entity[provider])

        return teams

    def encrypt(self, s: str):
        return self.fernet.encrypt(s.encode("ascii"))

    def decrypt(self, s: str):
        return self.fernet.decrypt(s).decode("ascii")

    async def setup_hook(self):
        for extension in self.config["discord"]["initial_cogs"]:
            await self.load_extension(extension)

        await Tortoise.init(
            db_url=f"sqlite://{self.config['db']['filename']}",
            modules={"models": ["les_louisdelatech.models"]},
        )
        await Tortoise.generate_schemas()

    def admin_sdk(self):
        creds = Credentials.from_service_account_file(
            self.google_path,
            scopes=self.config["google"]["scopes"]["admin"],
            subject=self.config["google"]["subject"],
        )

        return discovery.build(
            "admin", "directory_v1", credentials=creds, cache_discovery=False
        )

    def gmail_sdk(self, user: str):
        creds = Credentials.from_service_account_file(
            self.google_path,
            scopes=self.config["google"]["scopes"]["gmail"],
            subject=user,
        )

        return discovery.build("gmail", "v1", credentials=creds, cache_discovery=False)

    async def on_ready(self):
        logger.info(f"Logged in as: {self.user.name} - {self.user.id}")
        logger.info("Successfully logged in and booted...!")
        if not self.synced:  # check if slash commands have been synced
            await self.tree.sync()
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
        super()
