import random

import discord
from discord.ext import commands, tasks


class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_bot_activity.start()

    @tasks.loop(minutes=10.0)
    async def change_bot_activity(self):
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
