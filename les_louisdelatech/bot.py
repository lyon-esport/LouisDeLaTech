import logging
import os
import sys
import traceback

import discord
from cryptography.fernet import Fernet
from discord.ext import commands
from google.oauth2.service_account import Credentials
from googleapiclient import discovery
from tortoise import Tortoise, connections

logger = logging.getLogger(__name__)


class LouisDeLaTech(commands.Bot):
    def __init__(self, config, google_path):
        super().__init__(
            command_prefix=config["discord"]["command_prefix"],
            description="LouisDeLaTech is a discord bot manager for Lyon e-Sport",
        )

        self.root_dir = os.path.dirname(os.path.abspath(__file__))

        self.config = config
        self.google_path = google_path

        self.fernet = Fernet(self.config["db"]["secret_key"])

    def encrypt(self, s):
        return self.fernet.encrypt(s.encode("ascii"))

    def decrypt(self, s):
        return self.fernet.decrypt(s).decode("ascii")

    async def init_tortoise(self):
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

    def gmail_sdk(self, user):
        creds = Credentials.from_service_account_file(
            self.google_path,
            scopes=self.config["google"]["scopes"]["gmail"],
            subject=user,
        )

        return discovery.build("gmail", "v1", credentials=creds, cache_discovery=False)

    async def on_ready(self):
        logger.info(f"Logged in as: {self.user.name} - {self.user.id}")
        logger.info("Successfully logged in and booted...!")

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandNotFound):
            await ctx.send("Command not found")
        else:
            await ctx.send(f"Error while executing command => {error.__cause__}")
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )

    async def close(self):
        await connections.close_all()
        super()
