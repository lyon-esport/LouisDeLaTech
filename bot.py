import logging
import traceback
import sys

import discord
from discord.ext import tasks, commands
from googleapiclient import discovery
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)


class LouisDeLaTech(commands.Bot):
    def __init__(self, config, google_path):
        super().__init__(
            command_prefix=config["discord"]["command_prefix"],
            description="LouisDeLaTech is a discord bot manager for Lyon e-Sport",
        )

        self.config = config
        self.google_path = google_path

        self.credentials = Credentials.from_service_account_file(
            self.google_path,
            scopes=self.config["google"]["scopes"],
        )

    def admin_sdk(self):
        creds = self.credentials.with_subject(self.config["google"]["subject"])
        creds.refresh(Request())
        return discovery.build("admin", "directory_v1", credentials=creds)

    def gmail_sdk(self, impersonate_user):
        creds = self.credentials.with_subject(impersonate_user)
        creds.refresh(Request())
        return discovery.build("gmail", "v1", credentials=creds)

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
