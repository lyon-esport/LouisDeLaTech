import logging

import discord
import httpx
from discord.ext import commands
from discord.ext.commands import Context

logger = logging.getLogger(__name__)


class CatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cat", help="Get cat")
    async def get_cat(self, ctx: Context):
        async with httpx.AsyncClient() as client:
            cat_data = await client.get("https://api.thecatapi.com/v1/images/search")

        payload = cat_data.json()
        if not payload:
            return
        cat_url = payload[0]["url"]
        embed = discord.Embed(
            colour=discord.Colour.random(),
            title="Here is your kitty",
        ).set_image(url=cat_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CatCog(bot))
