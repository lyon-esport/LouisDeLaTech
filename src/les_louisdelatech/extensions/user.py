import logging
import asyncio
import os
from datetime import datetime

import discord
from discord.ext import commands
from discord.utils import get
from googleapiclient.errors import HttpError
from jinja2 import Template

from les_louisdelatech.utils.gsuite import (
    add_user,
    add_user_team,
    delete_user_group,
    format_google_api_error,
    get_users,
    is_gsuite_admin,
    is_user_managed,
    search_user,
    suspend_user,
    update_user_department,
    update_user_password,
    update_user_signature,
)
from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError
from les_louisdelatech.utils.email import send_email
from les_louisdelatech.utils.password import generate_password
from les_louisdelatech.utils.User import User

logger = logging.getLogger()


class UserCog(commands.Cog):
    """User lifecycle commands (provisioning/deprovisioning) across Discord + Google.

    Main flows:
    - `/provision`: create Google Workspace account, add to Google Groups, set Gmail
      signature, apply Discord roles/nickname, then send credentials by email.
    - `/deprovision`: suspend Google account and remove Discord roles.
    - `/uteam`: move a user to a different team (Google Groups + Discord roles + signature).
    - `/usignatures`: bulk update Gmail signatures.
    - `/rpassword`: reset Google password and send temporary password by email.
    """

    @commands.hybrid_command(help="Provision an user")
    @commands.guild_only()
    @is_gsuite_admin
    async def provision(
        self,
        ctx,
        member: discord.Member = commands.parameter(description="Discord user"),
        firstname: str = commands.parameter(description="User firstname"),
        lastname: str = commands.parameter(description="User lastname"),
        email: str = commands.parameter(description="User personal email (backup)"),
        birthdate: str = commands.parameter(
            description="User birthdate like 28/02/2023"
        ),
        address: str = commands.parameter(description="User address"),
        phone: str = commands.parameter(description="User phone number"),
        tee_shirt: str = commands.parameter(description="User tee shirt size"),
        pseudo: str = commands.parameter(description="User pseudo"),
        team_name: str = commands.parameter(description="User team"),
    ):
        """
        Provision an user
        [Discord]
            => User will be added to default group
            => User will be added to team group
        [Google]
            => User will be created and added to team group
        """
        await ctx.defer()
        team = self.bot.config["teams"].get(team_name, None)
        password = generate_password()
        admin_sdk = self.bot.admin_sdk()
        signature_template = Template(
            open(
                os.path.join(
                    self.bot.root_dir, "./templates/google/gmail_signature.j2"
                ),
                encoding="utf-8",
            ).read()
        )

        if team is None:
            await ctx.send(f"Team {team_name} is not managed by bot")
            return
        elif not team["team_role"]:
            await ctx.send(f"Team {team_name} is not a team role")
            return

        user = User(
            firstname,
            lastname,
            datetime.strptime(birthdate, "%d/%m/%Y"),
            pseudo,
            member.id,
            None,
            # `email` parameter is the *personal* email used as Google recovery email.
            # The Workspace email is derived from firstname/lastname by `User.email_from_name()`.
            email,
            phone,
            address,
            tee_shirt,
            team_name,
        )

        try:
            # Create the Workspace account then add it to the team Google Group.
            add_user(admin_sdk, user, password)
            add_user_team(admin_sdk, user, team["google_email"])

            # Practical workaround: Google APIs can be eventually consistent. If we
            # update Gmail settings too quickly, we can hit transient errors.
            await asyncio.sleep(5)

            update_user_signature(
                self.bot.gmail_sdk(user.email),
                signature_template,
                user,
                team["team_role"],
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
                    f":no_entry: Discord role {role_name} does not exist on server, check bot config"
                )
                return
        role = get(member.guild.roles, name=team["discord"])
        if role:
            await member.add_roles(role)
        else:
            await ctx.send(
                f":no_entry: Discord role {role_name} does not exist on discord server"
            )
            return

        await member.edit(nick=user.discord_name(firstname, pseudo, lastname))

        await ctx.send(f"User {user.email} provisionned")

        base_template = Template(
            open(
                os.path.join(self.bot.root_dir, "./templates/discord/base.j2"),
                encoding="utf-8",
            ).read()
        )
        body = base_template.render({"email": user.email, "password": password})

        team_template = Template(
            open(
                os.path.join(
                    self.bot.root_dir,
                    f"./templates/discord/{team['message_template']}",
                ),
                encoding="utf-8",
            ).read()
        )
        team_message = team_template.render()
        if team_message:
            body = f"{body}\n\n{team_message}"

        # Do not send passwords via Discord DM (often disabled). Email the user instead.
        if not user.backup_email:
            await ctx.send(
                ":no_entry: No personal email (backup_email) available to send credentials."
            )
            return
        if not self.bot.config["google"]["subject"]:
            await ctx.send(
                ":no_entry: google.subject is missing in config; cannot send emails."
            )
            return

        try:
            # Sender is the delegated mailbox `google.subject`.
            send_email(
                self.bot.mailer_sdk(),
                from_addr=self.bot.config["google"]["subject"],
                to_addr=user.backup_email,
                subject="Bienvenue a Lyon e-Sport - Acces Google Workspace",
                body=body,
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(help="Deprovision an user")
    @commands.guild_only()
    @is_gsuite_admin
    async def deprovision(
        self,
        ctx,
        member: discord.Member = commands.parameter(description="Discord user"),
    ):
        """
        [Discord]
            => User will be removed from all groups
        [Google]
            => User will be suspended
        """
        await ctx.defer()
        try:
            user = User.from_google(
                search_user(self.bot.admin_sdk(), member.name, member.id)
            )
            is_user_managed(
                user,
                self.bot.get_entity_to_skip("teams", "google"),
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{member} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        try:
            suspend_user(self.bot.admin_sdk(), user)
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        await member.edit(roles=[])

        await ctx.send(f":white_check_mark: User {member.name} deprovisionned")

    @commands.hybrid_command(name="uteam", help="Update user team")
    @commands.guild_only()
    @is_gsuite_admin
    async def update_team(
        self,
        ctx,
        member: discord.Member = commands.parameter(description="Discord user"),
        new_team_name: str = commands.parameter(description="New team name"),
    ):
        """
        [Discord]
            => User will be removed from all team groups
            => User will be added to this new team
        [Google]
            => User will be removed from all team groups
            => User will be added to this new team
            => User signature will be updated
        """
        await ctx.defer()
        try:
            user = User.from_google(
                search_user(self.bot.admin_sdk(), member.name, member.id)
            )
            is_user_managed(
                user,
                self.bot.get_entity_to_skip("teams", "google"),
            )
            user.team = new_team_name
        except LouisDeLaTechError as e:
            await ctx.send(f"{member} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        new_user_team = self.bot.config["teams"].get(user.team, None)
        admin_sdk = self.bot.admin_sdk()
        signature_template = Template(
            open(
                os.path.join(
                    self.bot.root_dir, "./templates/google/gmail_signature.j2"
                ),
                encoding="utf-8",
            ).read()
        )

        if new_user_team is None:
            await ctx.send(
                f":no_entry: Role {new_team_name} does not exist, check bot config"
            )
            return
        elif not new_user_team["team_role"]:
            await ctx.send(
                f":no_entry: Role {new_user_team} is invalid, check bot config"
            )
            return

        try:
            for v in self.bot.config["teams"].values():
                delete_user_group(admin_sdk, user, v["google_email"])
            add_user_team(admin_sdk, user, new_user_team["google_email"])
            update_user_department(admin_sdk, user)
            update_user_signature(
                self.bot.gmail_sdk(user.email),
                signature_template,
                user,
                new_user_team["team_role"],
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        if new_user_team is None:
            await ctx.send(
                f":no_entry: Role {user.team} does not exist, check bot config"
            )
            return

        for v in self.bot.config["teams"].values():
            role = get(member.guild.roles, name=v["discord"])
            if role:
                await member.remove_roles(role)
            else:
                await ctx.send(
                    f":no_entry: Discord role {v['discord']} does not exist, check bot config"
                )
                return
        role = get(member.guild.roles, name=new_user_team["discord"])
        if role:
            await member.add_roles(role)
        else:
            await ctx.send(f":no_entry: Discord role {user.team} does not exist")
            return

        await ctx.send(
            f":white_check_mark: User {member.name} is now member of team: {user.team}"
        )

    @commands.hybrid_command(
        name="usignatures", help="Update the signature of all users on gmail"
    )
    @commands.guild_only()
    @is_gsuite_admin
    async def update_signatures(self, ctx):
        await ctx.defer()
        user_updated = 0
        try:
            users = get_users(self.bot.admin_sdk())
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        signature_template = Template(
            open(
                os.path.join(
                    self.bot.root_dir, "./templates/google/gmail_signature.j2"
                ),
                encoding="utf-8",
            ).read()
        )

        await ctx.send(f"Starting to update {len(users)} users")
        for _user in users:
            try:
                user = User.from_google(_user)
                is_user_managed(
                    user,
                    self.bot.get_entity_to_skip("teams", "google"),
                )
                user_team = self.bot.config["teams"].get(user.team, None)
                update_user_signature(
                    self.bot.gmail_sdk(user.email),
                    signature_template,
                    user,
                    user_team["team_role"],
                )
                user_updated += 1
            except LouisDeLaTechError as e:
                await ctx.send(f"{e.args[0]}")
                continue
            except HttpError as e:
                await ctx.send(format_google_api_error(e))
                return

        await ctx.send(
            f":white_check_mark: Updated signatures for {user_updated}/{len(users)} users"
        )

    @commands.hybrid_command(help="Reset password of an user")
    @commands.guild_only()
    @is_gsuite_admin
    async def rpassword(
        self,
        ctx,
        member: discord.Member = commands.parameter(description="Discord user"),
    ):
        await ctx.defer()
        try:
            user = User.from_google(
                search_user(self.bot.admin_sdk(), member.name, member.id)
            )
            is_user_managed(
                user,
                self.bot.get_entity_to_skip("teams", "google"),
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{member} => {e.args[0]}")
            return
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        temp_pass = generate_password()

        template = Template(
            open(
                os.path.join(
                    self.bot.root_dir, "./templates/discord/reset_password.j2"
                ),
                encoding="utf-8",
            ).read()
        )

        try:
            update_user_password(self.bot.admin_sdk(), user, temp_pass, True)
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        if not user.backup_email:
            await ctx.send(
                f":no_entry: No personal email (backup_email) found for {member.name}; cannot send reset password."
            )
            return
        if not self.bot.config["google"]["subject"]:
            await ctx.send(
                ":no_entry: google.subject is missing in config; cannot send emails."
            )
            return

        try:
            send_email(
                self.bot.mailer_sdk(),
                from_addr=self.bot.config["google"]["subject"],
                to_addr=user.backup_email,
                subject="Reset mot de passe - Lyon e-Sport Workspace",
                body=template.render({"email": user.email, "password": temp_pass}),
            )
        except HttpError as e:
            await ctx.send(format_google_api_error(e))
            raise

        await ctx.send(
            f":white_check_mark: Sent a new password to {member.name} by email"
        )


async def setup(bot):
    await bot.add_cog(UserCog(bot))
