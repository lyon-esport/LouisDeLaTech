"""Google Workspace (Gsuite) helpers.

This module wraps calls to Google Admin SDK and Gmail settings APIs.

Key ideas:
- "Identity" is keyed by the custom attribute `custom.discordId` stored on the
  Google user.
- Provisioning creates users, assigns groups, and configures Gmail signature.
"""

import logging
from functools import wraps
from http.client import responses

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError
from les_louisdelatech.utils.password import hash_password
from les_louisdelatech.utils.User import User

logger = logging.getLogger(__name__)


def is_gsuite_admin(func):
    """Decorator: allow command only if the caller is a Google Workspace admin."""

    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            user = User.from_google(
                search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
            )
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} {e.args[0]}")
            return None
        if not user.is_admin:
            await ctx.send(f"{ctx.author} you are not a Gsuite admin")
            logger.error(f"{ctx.author} you are not a Gsuite admin")
            return None
        return await func(self, ctx, *args, **kwargs)

    return wrapper


def format_google_api_error(error: HttpError):
    """Return a compact error string for display in Discord."""
    status = getattr(error, "status_code", None)
    if status:
        return (
            f"Google API error status code {status}:{responses.get(status, 'Unknown')}"
        )
    return f"Google API error: {error}"


def is_user_managed(user: User, teams_to_skip: list[str]):
    """Raise if a user's team is configured as out-of-scope for this bot."""
    if user.team in teams_to_skip:
        raise LouisDeLaTechError(
            f"Gsuite account not managed by this bot for this user: {user.email}"
        )


def user_is_in_group(admin_sdk: Resource, user: User, group_email: str):
    """Check if a user is a member of a Google Group."""
    return make_request(
        admin_sdk.members().hasMember(groupKey=group_email, memberKey=user.email)
    )["isMember"]


def get_users(admin_sdk: Resource):
    """List all users in the lyon-esport.fr domain (admin view, full projection)."""
    users = []
    resp = {"nextPageToken": None}
    while "nextPageToken" in resp:
        resp = make_request(
            admin_sdk.users().list(
                domain="lyon-esport.fr",
                projection="full",
                viewType="admin_view",
                pageToken=resp["nextPageToken"]
                if "nextPageToken" in resp and resp["nextPageToken"] is not None
                else None,
            )
        )
        users += resp["users"]

    return users


def search_user(admin_sdk: Resource, discord_pseudo, discord_id):
    """Find a Google user by Discord ID stored in the custom schema."""
    users = make_request(
        admin_sdk.users().list(
            query=f"custom.discordId={discord_id}",
            customer="my_customer",
            projection="full",
            viewType="admin_view",
        )
    )

    users = users["users"] if "users" in users else []

    if len(users) == 0:
        raise LouisDeLaTechError(
            f"No Gsuite account found with discordId: {discord_id} for user {discord_pseudo}"
        )
    elif len(users) > 1:
        raise LouisDeLaTechError(
            f"Multiple Gsuite users with same discordId: {discord_id} for user {discord_pseudo}"
        )

    return users[0]


def add_user(
    admin_sdk: Resource,
    user: User,
    password: str,
):
    """Create a Google Workspace user.

    Notes:
    - We provide password as SHA-1 hash because Google Admin API supports
      `hashFunction: SHA-1` for compatibility with existing flows.
    - Optional fields are only included if present to avoid 400 errors.
    """
    body = {
        "name": {
            "familyName": user.lastname,
            "givenName": user.firstname,
            "fullName": f"{user.firstname} {user.lastname}",
        },
        "primaryEmail": user.email,
        "customSchemas": {
            "custom": {
                "discordId": user.discord_id,
                "pseudo": user.pseudo,
                "teeShirt": user.tee_shirt,
                "birthdate": user.birthdate.strftime("%d/%m/%Y"),
            },
        },
        "organizations": [{"primary": True, "customType": "", "department": user.team}],
        "password": hash_password(password),
        "hashFunction": "SHA-1",
        "changePasswordAtNextLogin": True,
    }
    if user.address:
        body["addresses"] = [{"formatted": user.address}]
    if user.phone:
        body["phones"] = [{"type": "mobile", "value": user.phone, "primary": True}]
        body["recoveryPhone"] = user.phone
    if user.backup_email:
        body["emails"] = [{"type": "home", "address": user.backup_email}]
        body["recoveryEmail"] = user.backup_email
    make_request(admin_sdk.users().insert(body=body))


def update_user_signature(gmail_sdk: Resource, template, user: User, team_role: bool):
    """Update the Gmail signature for a user."""
    make_request(
        gmail_sdk.users()
        .settings()
        .sendAs()
        .update(
            userId=user.email,
            sendAsEmail=user.email,
            body={
                "signature": template.render(
                    {
                        "email": user.email,
                        "firstname": user.firstname,
                        "lastname": user.lastname,
                        "position": user.position,
                        "team": user.team if team_role else None,
                    }
                )
            },
        )
    )


def suspend_user(admin_sdk: Resource, user: User):
    """Suspend a Google user (soft deprovision)."""
    body = {"suspended": True}
    make_request(admin_sdk.users().update(userKey=user.email, body=body))


def update_user_department(admin_sdk: Resource, user: User):
    """Update the user's department (= team)."""
    body = {
        "organizations": [{"primary": True, "customType": "", "department": user.team}]
    }
    make_request(admin_sdk.users().update(userKey=user.email, body=body))


def update_user_password(
    admin_sdk: Resource, user: User, password: str, temporary_pass: bool
):
    """Set a user's password and optionally force change at next login."""
    body = {
        "password": hash_password(password),
        "hashFunction": "SHA-1",
        "changePasswordAtNextLogin": temporary_pass,
    }
    make_request(admin_sdk.users().update(userKey=user.email, body=body))


def add_user_team(admin_sdk: Resource, user: User, group_email: str):
    """Add a user to a Google Group."""
    body = {
        "email": user.email,
        "role": "MEMBER",
    }
    make_request(admin_sdk.members().insert(groupKey=group_email, body=body))


def delete_user_group(admin_sdk: Resource, user: User, group_email: str):
    """Remove a user from a Google Group if currently a member."""
    if user_is_in_group(admin_sdk, user, group_email):
        make_request(
            admin_sdk.members().delete(groupKey=group_email, memberKey=user.email)
        )


def make_request(req):
    """Single place to execute API requests (easy to extend with retries later)."""
    return req.execute()
