from discord.ext import commands


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="gteams", help="Get available teams")
    async def get_teams(self, ctx):
        message = "Available roles :\n```"

        for team in self.bot.config["teams"]:
            message += f"\n{team}"

        message += "```"
        await ctx.send(message)


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
