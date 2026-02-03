import logging

import pyotp
from discord.ext import commands
from googleapiclient.errors import HttpError
from tortoise.exceptions import DoesNotExist

from les_louisdelatech.models.otp import Digest, Otp
from les_louisdelatech.utils.discord import is_team_allowed
from les_louisdelatech.utils.gsuite import format_google_api_error, search_user
from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError
from les_louisdelatech.utils.User import User

logger = logging.getLogger()


class OtpCog(commands.Cog):
    """Commands to manage OTP secrets per team.

    Security model:
    - Secrets are stored encrypted in SQLite (see `models/otp.py` + `bot.encrypt`).
    - Users can only access OTPs for their own team (team is resolved from Google).
    - `/gotp` sends the generated code in DM to reduce leaking secrets in channels.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lotp", help="List otp code")
    @commands.guild_only()
    @is_team_allowed
    async def list_otp(self, ctx):
        """List OTP entries available for the caller's team."""
        await ctx.defer()
        try:
            user = User.from_google(
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

    @commands.hybrid_command(name="gotp", help="Get otp code")
    @commands.guild_only()
    @is_team_allowed
    async def get_otp(
        self, ctx, name: str = commands.parameter(description="Otp name")
    ):
        """Send the current TOTP code for a named OTP entry (DM)."""
        await ctx.defer()
        try:
            user = User.from_google(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        try:
            otp = await Otp.get(name=name, team=user.team)
        except DoesNotExist:
            await ctx.send(f":no_entry: Otp code {name} not found for team {user.team}")
            return
        totp = pyotp.TOTP(
            s=self.bot.decrypt(otp.secret),
            digest=otp.digest,
            digits=otp.digits,
            name=otp.name,
        )

        await ctx.author.send(f"Otp code for {name} is {totp.now()}")

        logger.info(f"Otp code {name} of team {user.team} send in DM to {ctx.author}")
        await ctx.send(
            f":white_check_mark: Otp code {name} of team {user.team} send in DM to {ctx.author}"
        )

    @commands.hybrid_command(name="cotp", help="Create otp code")
    @commands.guild_only()
    @is_team_allowed
    async def create_otp(
        self,
        ctx,
        name: str = commands.parameter(description="Otp name"),
        digest: str = commands.parameter(description="Otp digest"),
        digits: int = commands.parameter(description="Otp digits"),
        secret: str = commands.parameter(description="Otp secret"),
    ):
        """Create a new OTP entry for the caller's team.

        - `digest` must be one of sha1/sha256/sha512
        - `digits` must be between 6 and 10
        - `secret` is encrypted before storing
        """
        await ctx.defer()
        if ctx.message:
            await ctx.message.delete()

        try:
            user = User.from_google(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        try:
            digest_value = Digest(digest)
        except ValueError:
            await ctx.send(
                f":no_entry: Invalid digest '{digest}'. Allowed: {', '.join([d.value for d in Digest])}"
            )
            return

        if digits < 6 or digits > 10:
            await ctx.send(":no_entry: Digits must be between 6 and 10")
            return

        await Otp.create(
            name=name,
            team=user.team,
            digest=digest_value,
            digits=digits,
            secret=self.bot.encrypt(secret),
        )

        logger.info(f"Otp code {name} of team {user.team} created by {ctx.author}")
        await ctx.send(
            f":white_check_mark: Otp code {name} of team {user.team} created by {ctx.author}"
        )

    @commands.hybrid_command(name="dotp", help="Delete otp code")
    @commands.guild_only()
    @is_team_allowed
    async def delete_otp(
        self, ctx, name: str = commands.parameter(description="Otp name")
    ):
        await ctx.defer()
        try:
            user = User.from_google(
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
        await ctx.send(
            f":white_check_mark: Otp code {name} of team {user.team} deleted by {ctx.author}"
        )


async def setup(bot):
    await bot.add_cog(OtpCog(bot))
