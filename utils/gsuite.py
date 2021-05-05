import logging
from functools import wraps
from http.client import responses

from jinja2 import Template

from utils.LouisDeLaTechError import LouisDeLaTechError
from utils.User import User

logger = logging.getLogger(__name__)


def is_gsuite_admin(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            user = search_user(self.bot.admin_sdk(), ctx.author.name, ctx.author.id)
        except LouisDeLaTechError as e:
            await ctx.send(f"{ctx.author} {e.args[0]}")
            return None
        if not user.is_admin:
            await ctx.send(f"{ctx.author} you are not a Gsuite admin")
            logger.error(f"{ctx.author} you are not a Gsuite admin")
            return None
        return await func(self, ctx, *args, **kwargs)

    return wrapper


def format_google_api_error(error):
    return f"Google API error status code {error.status_code}:{responses[error.status_code]}"


def get_users(admin_sdk):
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


def search_user(admin_sdk, discord_pseudo, discord_id):
    users = make_request(
        admin_sdk.users().list(
            query=f"custom.discord_id={discord_id}",
            customer="my_customer",
            projection="full",
            viewType="admin_view",
        )
    )
    users = users["users"] if "users" in users else None
    if len(users) == 0:
        raise LouisDeLaTechError(
            f"No Gsuite account found with discord_id: {discord_id} for user {discord_pseudo}"
        )
    elif len(users) > 1:
        raise LouisDeLaTechError(
            f"Multiple Gsuite users with same discord_id: {discord_id} for user {discord_pseudo}"
        )
    elif discord_id != users[0]["customSchemas"]["custom"]["discord_id"]:
        raise LouisDeLaTechError(
            f"Stupid API send me an other user that does not match discord_id: {discord_id} for user {discord_pseudo}"
        )

    return User(users[0])


def add_user(
    admin_sdk, firstname, lastname, email, password, group, discord_id, pseudo
):
    body = {
        "name": {
            "familyName": lastname,
            "givenName": firstname,
            "fullName": f"{firstname.title()} {lastname.title()}",
        },
        "primaryEmail": email,
        "customSchemas": {
            "custom": {
                "discord_id": discord_id,
                "pseudo": pseudo,
            },
        },
        "organizations": [{"primary": True, "customType": "", "department": group}],
        "password": password,
        "changePasswordAtNextLogin": True,
    }
    make_request(admin_sdk.users().insert(body=body))


def update_user_pseudo(admin_sdk, user_email, pseudo):
    body = {
        "customSchemas": {
            "custom": {
                "pseudo": pseudo,
            },
        },
    }
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def update_user_signature(gmail_sdk, user_email, firstname, lastname, role, team):
    template = Template(
        open("./templates/google/gmail_signature.j2", encoding="utf-8").read()
    )
    make_request(
        gmail_sdk.users()
        .settings()
        .sendAs()
        .update(
            userId=user_email,
            sendAsEmail=user_email,
            body={
                "signature": template.render(
                    {
                        "email": user_email,
                        "firstname": firstname,
                        "lastname": lastname,
                        "role": role,
                        "team": team,
                    }
                )
            },
        )
    )


def suspend_user(admin_sdk, user_email, author):
    body = {"suspended": True, "suspensionReason": f"Account deprovisioned by {author}"}
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def add_user_group(admin_sdk, user_email, group_email):
    body = {
        "email": user_email,
        "role": "MEMBER",
    }
    make_request(admin_sdk.members().insert(groupKey=group_email, body=body))


def user_is_in_group(admin_sdk, user_email, group_email):
    return make_request(
        admin_sdk.members().hasMember(groupKey=group_email, memberKey=user_email)
    )["isMember"]


def delete_user_group(admin_sdk, user_email, group_email):
    if user_is_in_group(admin_sdk, user_email, group_email):
        make_request(
            admin_sdk.members().delete(groupKey=group_email, memberKey=user_email)
        )


def make_request(req):
    return req.execute()
