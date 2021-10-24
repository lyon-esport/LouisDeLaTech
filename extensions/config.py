from discord.ext import commands


class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gteams", help="Get available teams")
    async def get_teams(self, ctx):
        message = "Available roles :\n```"

        for team in self.bot.config["teams"]:
            message += f"\n{team}"

        message += "```"
        await ctx.send(message)


def setup(bot):
    bot.add_cog(TaskCog(bot))
