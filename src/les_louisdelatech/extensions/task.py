import logging
import random

import discord
from discord.ext import commands, tasks

logger = logging.getLogger()


class TaskCog(commands.Cog):
    """Background tasks for the bot.

    Currently only rotates the bot presence/activity every 10 minutes based on
    `discord.bot_activity` in config.
    """

    def __init__(self, bot):
        self.bot = bot
        self.change_bot_activity.start()

    @tasks.loop(minutes=10.0)
    async def change_bot_activity(self):
        if not self.bot.config["discord"]["bot_activity"]:
            logger.warning("Bot activity list is empty; skipping presence update.")
            return
        activity = random.choice(self.bot.config["discord"]["bot_activity"])
        await self.bot.change_presence(
            activity=discord.Game(activity), status=discord.Status.online
        )

    @change_bot_activity.before_loop
    async def before_send(self):
        await self.bot.wait_until_ready()

        return


async def setup(bot):
    await bot.add_cog(TaskCog(bot))
