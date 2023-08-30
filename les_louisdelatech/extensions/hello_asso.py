import logging

from discord.ext import commands

from les_louisdelatech.utils.gsuite import get_users, is_gsuite_admin, is_user_managed
from les_louisdelatech.utils.hello_asso import get_orders
from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError
from les_louisdelatech.utils.User import User

logger = logging.getLogger()


class HelloAssoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ha_check_update", help="Check users")
    @commands.guild_only()
    @is_gsuite_admin
    async def ha_check_update(
        self,
        ctx,
        form_slug: str = commands.parameter(description="Form slug name"),
    ):
        """
        Display new and updated users
        """
        new_user_count = 0
        updated_user_count = 0

        current_users = []
        for current_user in get_users(self.bot.admin_sdk()):
            try:
                user = User.from_google(current_user)
                is_user_managed(
                    user,
                    self.bot.get_entity_to_skip("teams", "google"),
                )
                current_users.append(user)
            except LouisDeLaTechError as e:
                await ctx.send(e.args[0])
                continue
        membership_orders = get_orders(
            self.bot.hello_asso,
            self.bot.config["hello_asso"]["organization"],
            "Membership",
            form_slug,
        )

        for membership in membership_orders:
            try:
                user = User.from_hello_asso(membership)
            except LouisDeLaTechError as e:
                logger.debug(ctx.send(e.args[0]))
                continue
            except ValueError as e:
                await ctx.send(ctx.send(e.args[0]))
                continue

            for current_user in current_users:
                if user == current_user:
                    user_diff = user.attr_differ(current_user)
                    if len(user_diff) > 0:
                        await ctx.send(
                            f":arrows_counterclockwise: Update user : {user.firstname} {user.lastname} [{', '.join(user_diff)}] needs an update"
                        )
                        updated_user_count += 1
                    break
            else:
                await ctx.send(f":new: New user : {user.firstname} {user.lastname}")
                new_user_count += 1

        await ctx.send(
            f":white_check_mark: {new_user_count} users to create and {updated_user_count} users to update"
        )

    @commands.hybrid_command(name="ha_verify_payment", help="Check payments")
    @commands.guild_only()
    @is_gsuite_admin
    async def ha_verify_payment(
        self,
        ctx,
        form_slug: str = commands.parameter(description="Form slug name"),
    ):
        """
        Display users who haven't paid
        """
        unpaid_user_count = 0

        current_users = get_users(self.bot.admin_sdk())
        membership_orders = []
        for membership_order in get_orders(
            self.bot.hello_asso,
            self.bot.config["hello_asso"]["organization"],
            "Membership",
            form_slug,
        ):
            try:
                user = User.from_hello_asso(membership_order)
                membership_orders.append(user)
            except LouisDeLaTechError as e:
                logger.debug(ctx.send(e.args[0]))
                continue
            except ValueError as e:
                await ctx.send(ctx.send(e.args[0]))
                continue

        for current_user in current_users:
            try:
                user = User.from_google(current_user)
                is_user_managed(
                    user,
                    self.bot.get_entity_to_skip("teams", "google"),
                )
            except LouisDeLaTechError as e:
                await ctx.send(e.args[0])
                continue

            if user not in membership_orders:
                await ctx.send(f"User did not pay : {user.firstname} {user.lastname}")
                unpaid_user_count += 1

        await ctx.send(f":white_check_mark: {unpaid_user_count} users did not pay")


async def setup(bot):
    await bot.add_cog(HelloAssoCog(bot))
