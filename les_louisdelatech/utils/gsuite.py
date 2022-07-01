import logging
from functools import wraps
from http.client import responses

from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError
from les_louisdelatech.utils.User import User

logger = logging.getLogger(__name__)


def is_gsuite_admin(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            user = User(
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


def format_google_api_error(error):
    return f"Google API error status code {error.status_code}:{responses[error.status_code]}"


def is_user_managed(admin_sdk, user_email, teams_to_skip):
    user = make_request(
        admin_sdk.users().get(
            userKey=user_email, projection="full", viewType="admin_view"
        )
    )

    if user is None:
        raise LouisDeLaTechError(f"No Gsuite account found for user: {user_email}")

    if User(user).team in teams_to_skip:
        raise LouisDeLaTechError(
            f"Gsuite account not managed by this bot for this user: {user_email}"
        )


def user_is_in_group(admin_sdk, user_email, group_email):
    return make_request(
        admin_sdk.members().hasMember(groupKey=group_email, memberKey=user_email)
    )["isMember"]


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
                "discordId": discord_id,
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


def update_user_signature(
    gmail_sdk, template, user_email, firstname, lastname, role, team, team_role
):
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
                        "team": team if team_role else None,
                    }
                )
            },
        )
    )


def suspend_user(admin_sdk, user_email):
    body = {"suspended": True}
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def update_user_department(admin_sdk, user_email, department):
    body = {
        "organizations": [{"primary": True, "customType": "", "department": department}]
    }
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def update_user_password(admin_sdk, user_email, password, temporary_pass):
    body = {
        "password": password,
        "changePasswordAtNextLogin": temporary_pass,
    }
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def update_user_recovery(admin_sdk, user_email, recovery_email):
    body = {"recoveryEmail": recovery_email}
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def add_user_group(admin_sdk, user_email, group_email):
    body = {
        "email": user_email,
        "role": "MEMBER",
    }
    make_request(admin_sdk.members().insert(groupKey=group_email, body=body))


def delete_user_group(admin_sdk, user_email, group_email):
    if user_is_in_group(admin_sdk, user_email, group_email):
        make_request(
            admin_sdk.members().delete(groupKey=group_email, memberKey=user_email)
        )


def make_request(req):
    return req.execute()
