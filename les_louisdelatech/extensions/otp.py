import logging

import pyotp
from discord.ext import commands
from googleapiclient.errors import HttpError

from les_louisdelatech.models.otp import Otp
from les_louisdelatech.utils.discord import is_team_allowed
from les_louisdelatech.utils.gsuite import format_google_api_error, search_user
from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError
from les_louisdelatech.utils.User import User

logger = logging.getLogger(__name__)


class OtpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lotp", help="List otp code")
    @commands.guild_only()
    @is_team_allowed
    async def list_otp(self, ctx):
        try:
            user = User(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        otps = await Otp.filter(team=user.team)

        message = f"Otp code available for team {user.team} :\n```"
        if len(otps) > 0:
            for o in otps:
                message += f"\n{o.name}"
        else:
            message += "No Otp code available"
        message += "```"

        await ctx.send(message)

    @commands.command(name="gotp", help="Get otp code")
    @commands.guild_only()
    @is_team_allowed
    async def get_otp(self, ctx, name):
        try:
            user = User(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        otp = await Otp.get(name=name, team=user.team)
        totp = pyotp.TOTP(
            s=self.bot.decrypt(otp.secret),
            digest=otp.digest,
            digits=otp.digits,
            name=otp.name,
        )

        await ctx.author.send(f"Otp code for {name} is {totp.now()}")

        logger.info(f"Otp code {name} of team {user.team} send in DM to {ctx.author}")
        await ctx.send(
            f"Otp code {name} of team {user.team} send in DM to {ctx.author}"
        )

    @commands.command(name="cotp", help="Create otp code")
    @commands.guild_only()
    @is_team_allowed
    async def create_otp(self, ctx, name, digest, digits, secret):
        await ctx.message.delete()

        try:
            user = User(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        await Otp.create(
            name=name,
            team=user.team,
            digest=digest,
            digits=digits,
            secret=self.bot.encrypt(secret),
        )

        logger.info(f"Otp code {name} of team {user.team} created by {ctx.author}")
        await ctx.send(f"Otp code {name} of team {user.team} created by {ctx.author}")

    @commands.command(name="dotp", help="Delete otp code")
    @commands.guild_only()
    @is_team_allowed
    async def delete_otp(self, ctx, name):
        try:
            user = User(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        await Otp.filter(name=name, team=user.team).delete()

        logger.info(f"Otp code {name} of team {user.team} deleted by {ctx.author}")
        await ctx.send(f"Otp code {name} of team {user.team} deleted by {ctx.author}")


def setup(bot):
    bot.add_cog(OtpCog(bot))
