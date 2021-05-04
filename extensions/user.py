import logging

import discord
from discord.ext import commands
from discord.utils import get
from googleapiclient.errors import HttpError
from jinja2 import Template

from utils.gsuite import (
    add_user,
    update_user_names,
    suspend_user,
    add_user_group,
    delete_user_group,
    update_user_signature,
    is_gsuite_admin,
)
from utils.format import (
    format_discord_name,
    format_gsuite_email,
    format_google_api_error,
)
from utils.password import generate_password

logger = logging.getLogger(__name__)


class UserCog(commands.Cog):
    @commands.command(help="Provision an user")
    @commands.guild_only()
    @is_gsuite_admin
    async def provision(
        self, ctx, member: discord.Member, firstname, lastname, pseudo, new_role_name
    ):
        """
        Provision an user
        [Discord]
            => User will be added to default group
            => User will be added to team group
        [Google]
            => User will be created and added to team group
        """
        user_email = format_gsuite_email(firstname, lastname)
        user_team = self.bot.config["teams"].get(new_role_name, None)
        password = generate_password()
        admin_sdk = self.bot.admin_sdk()

        try:
            add_user(
                admin_sdk,
                firstname,
                lastname,
                user_email,
                password,
                new_role_name,
                member.id,
                pseudo,
            )
            add_user_group(admin_sdk, user_email, user_team["google"])
            update_user_signature(self.bot.gmail_sdk(user_email), user_email)
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        if user_team is None:
            await ctx.send(f"Role {new_role_name} does not exist, check bot config")
            return

        for role_name in self.bot.config["discord"]["roles"]["default"]:
            role = get(member.guild.roles, name=role_name)
            if role:
                await member.add_roles(role)
            else:
                await ctx.send(
                    f"Discord role {role_name} does not exist on server, check bot config"
                )
                return
        role = get(member.guild.roles, name=user_team["discord"])
        if role:
            await member.add_roles(role)
        else:
            await ctx.send(
                f"Discord role {new_role_name} does not exist on discord server"
            )
            return

        await member.edit(nick=format_discord_name(firstname, lastname, pseudo))

        await ctx.send(f"User {member.name} provisionned")

        template = Template(
            open("./templates/discord/base.j2", encoding="utf-8").read()
        )
        await member.send(template.render({"email": user_email, "password": password}))

        template = Template(
            open(
                f"./templates/discord/{user_team['message_template']}", encoding="utf-8"
            ).read()
        )
        await member.send(template.render())

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_gsuite_admin
    async def test(self, ctx):
        await ctx.send("test")

    @commands.command(help="Deprovision an user")
    @commands.guild_only()
    @is_gsuite_admin
    async def deprovision(self, ctx, member: discord.Member, firstname, lastname):
        """
        [Discord]
            => User will be removed from all groups
        [Google]
            => User will be suspended
        """
        user_email = format_gsuite_email(firstname, lastname)
        try:
            suspend_user(self.bot.admin_sdk(), user_email, ctx.author)
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        await member.edit(roles=[])

        await ctx.send(f"User {member.name} deprovisionned")

    @commands.command(name="uteam", help="Update user team")
    @commands.guild_only()
    @is_gsuite_admin
    async def update_team(
        self, ctx, member: discord.Member, firstname, lastname, new_role_name
    ):
        """
        [Discord]
            => User will be removed from all team groups
            => User will be added to this new team
        [Google]
            => User will be removed from all team groups
            => User will be added to this new team
        """
        user_team = self.bot.config["teams"].get(new_role_name, None)
        admin_sdk = self.bot.admin_sdk()

        try:
            for v in self.bot.config["teams"].values():
                delete_user_group(
                    admin_sdk, format_gsuite_email(firstname, lastname), v["google"]
                )
            add_user_group(
                admin_sdk, format_gsuite_email(firstname, lastname), user_team["google"]
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        if user_team is None:
            await ctx.send(f"Role {new_role_name} does not exist, check bot config")
            return

        for v in self.bot.config["teams"].values():
            role = get(member.guild.roles, name=v["discord"])
            if role:
                await member.remove_roles(role)
            else:
                await ctx.send(
                    f"Discord role {v['discord']} does not exist, check bot config"
                )
                return
        role = get(member.guild.roles, name=user_team["discord"])
        if role:
            await member.add_roles(role)
        else:
            await ctx.send(f"Discord role {new_role_name} does not exist")
            return

        await ctx.send(f"User {member.name} is now member of {new_role_name}")

    @commands.command(name="upseudo", help="Update user pseudo")
    @commands.guild_only()
    @is_gsuite_admin
    async def update_pseudo(
        self, ctx, member: discord.Member, firstname, lastname, new_pseudo
    ):
        """
        [Discord]
            => User will be renamed
        [Google]
            => User will be renamed
        """
        try:
            update_user_names(
                self.bot.admin_sdk(),
                firstname,
                lastname,
                new_pseudo,
                format_gsuite_email(firstname, lastname),
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        old_nick = member.nick

        await member.edit(nick=format_discord_name(firstname, lastname, new_pseudo))

        await ctx.send(f"User {old_nick} is now {member.nick}")


def setup(bot):
    bot.add_cog(UserCog(bot))
