import logging

import discord
from discord.ext import commands
from discord.utils import get
from googleapiclient.errors import HttpError
from jinja2 import Template

from utils.LouisDeLaTechError import LouisDeLaTechError
from utils.User import User
from utils.gsuite import (
    search_user,
    get_users,
    add_user,
    update_user_pseudo,
    update_user_department,
    suspend_user,
    add_user_group,
    delete_user_group,
    update_user_signature,
    is_gsuite_admin,
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
        user_email = User.email_from_name(firstname, lastname)
        user_team = self.bot.config["teams"].get(new_role_name, None)
        password = generate_password()
        admin_sdk = self.bot.admin_sdk()

        if user_team is None:
            await ctx.send(f"Role {new_role_name} does not exist, check bot config")
            return

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
            update_user_signature(
                self.bot.gmail_sdk(user_email),
                user_email,
                firstname,
                lastname,
                None,
                new_role_name,
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

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

        await member.edit(nick=User.discord_name(firstname, pseudo, lastname))

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
        team_message = template.render()
        if team_message:
            await member.send(team_message)

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Deprovision an user")
    @commands.guild_only()
    @is_gsuite_admin
    async def deprovision(self, ctx, member: discord.Member):
        """
        [Discord]
            => User will be removed from all groups
        [Google]
            => User will be suspended
        """
        try:
            user = search_user(self.bot.admin_sdk(), member.name, member.id)
        except LouisDeLaTechError as e:
            await ctx.send(f"{member} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise
        try:
            suspend_user(self.bot.admin_sdk(), user.email, ctx.author)
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        await member.edit(roles=[])

        await ctx.send(f"User {member.name} deprovisionned")

    @commands.command(name="uteam", help="Update user team")
    @commands.guild_only()
    @is_gsuite_admin
    async def update_team(self, ctx, member: discord.Member, new_team_name):
        """
        [Discord]
            => User will be removed from all team groups
            => User will be added to this new team
        [Google]
            => User will be removed from all team groups
            => User will be added to this new team
            => User signature will be updated
        """
        try:
            user = search_user(self.bot.admin_sdk(), member.name, member.id)
            user.team = new_team_name
        except LouisDeLaTechError as e:
            await ctx.send(f"{member} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        new_user_team = self.bot.config["teams"].get(user.team, None)
        admin_sdk = self.bot.admin_sdk()

        if new_user_team is None:
            await ctx.send(f"Role {user.team} does not exist, check bot config")
            return

        try:
            for v in self.bot.config["teams"].values():
                delete_user_group(admin_sdk, user.email, v["google"])
            add_user_group(admin_sdk, user.email, new_user_team["google"])
            update_user_department(admin_sdk, user.email, user.team)
            update_user_signature(
                self.bot.gmail_sdk(user.email),
                user.email,
                user.firstname,
                user.lastname,
                user.role,
                user.team,
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        if new_user_team is None:
            await ctx.send(f"Role {user.team} does not exist, check bot config")
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
        role = get(member.guild.roles, name=new_user_team["discord"])
        if role:
            await member.add_roles(role)
        else:
            await ctx.send(f"Discord role {user.team} does not exist")
            return

        await ctx.send(f"User {member.name} is now member of {user.team}")

    @commands.command(name="upseudo", help="Update user pseudo")
    @commands.guild_only()
    @is_gsuite_admin
    async def update_pseudo(self, ctx, member: discord.Member, new_pseudo):
        """
        [Discord]
            => User will be renamed
        [Google]
            => User pseudo will be renamed
        """
        try:
            user = search_user(self.bot.admin_sdk(), member.name, member.id)
            user.pseudo = new_pseudo
        except LouisDeLaTechError as e:
            await ctx.send(f"{member} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        try:
            update_user_pseudo(
                self.bot.admin_sdk(),
                user.email,
                user.pseudo,
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        old_nick = member.nick

        await member.edit(
            nick=User.discord_name(user.firstname, user.pseudo, user.lastname)
        )

        await ctx.send(f"User {old_nick} is now {member.nick}")

    @commands.command(
        name="usignatures", help="Update the signature of all users on gmail"
    )
    @commands.guild_only()
    @is_gsuite_admin
    async def update_signatures(self, ctx):
        user_updated = 0
        try:
            users = get_users(self.bot.admin_sdk())
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        for user in users:
            try:
                user = User(user)
                update_user_signature(
                    self.bot.gmail_sdk(user.email),
                    user.email,
                    user.firstname,
                    user.lastname,
                    user.role,
                    user.team,
                )
                user_updated += 1
            except LouisDeLaTechError as e:
                await ctx.send(f"{user['primaryEmail']} => {e.args[0]}")
                continue
            except HttpError as e:
                await ctx.send(format_google_api_error(e))
                return

        await ctx.send(f"Update signatures for {user_updated}/{len(users)} users")


def setup(bot):
    bot.add_cog(UserCog(bot))
