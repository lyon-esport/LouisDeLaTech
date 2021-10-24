from discord.ext import commands

from utils.discord import is_team_allowed


class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Change channel topic")
    @is_team_allowed
    async def topic(self, ctx, description):
        await ctx.channel.edit(topic=description)
        await ctx.send("Channel topic updated")


def setup(bot):
    bot.add_cog(TaskCog(bot))
