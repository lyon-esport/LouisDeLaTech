import logging
from functools import wraps

from jinja2 import Template


logger = logging.getLogger(__name__)


def is_gsuite_admin(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        users = get_users(self.bot.admin_sdk(), ctx.author.id)
        if "users" not in users:
            await ctx.send("No Gsuite account with your discord_id")
            logger.error("No Gsuite account with your discord_id")
            return None
        else:
            users = users["users"]
        if len(users) == 1 and not users[0]["isAdmin"]:
            await ctx.send("You are not a Gsuite admin")
            logger.error("You are not a Gsuite admin")
            return None
        elif len(users) > 1:
            await ctx.send("Multiple Gsuite users with same discord_id")
            logger.error("Multiple Gsuite users with same discord_id")
            return None
        return await func(self, ctx, *args, **kwargs)

    return wrapper


def get_users(admin_sdk, discord_id):
    return make_request(
        admin_sdk.users().list(
            query=f"custom.discord_id={discord_id}",
            customer="my_customer",
            projection="full",
            viewType="admin_view",
        )
    )


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


def update_user_names(admin_sdk, firstname, lastname, pseudo, user_email):
    body = {
        "name": {
            "familyName": lastname,
            "givenName": firstname,
            "fullName": f"{firstname.title()} {lastname.title()}",
        },
        "customSchemas": {
            "custom": {
                "pseudo": pseudo,
            },
        },
    }
    make_request(admin_sdk.users().update(userKey=user_email, body=body))


def update_user_signature(gmail_sdk, user_email):
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
            body={"signature": template.render()},
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
