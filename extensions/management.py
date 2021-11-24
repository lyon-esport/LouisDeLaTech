from discord.ext import commands

from utils.discord import is_team_allowed


class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Change channel topic")
    @is_team_allowed
    async def topic(self, ctx, description):
        await ctx.channel.edit(topic=description)
        await ctx.send("Channel topic updated")

    # Meeting voice channel creation & deletion listener
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Create voice channel
        if (
            after.channel
            and after.channel.name
            == self.bot.config["voice_channel_creation"]["trigger_channel_name"]
            and not member.bot
        ):
            list_channels_name = []

            for channel in after.channel.category.voice_channels:
                if channel.name.startswith(
                    self.bot.config["voice_channel_creation"]["new_channel_name"]
                ):
                    list_channels_name.insert(len(list_channels_name), channel.name)
            # temp debug
            # print(list_channels_name)

            newchannel = await member.guild.create_voice_channel(
                self.bot.config["voice_channel_creation"]["new_channel_name"],
                overwrites=None,
                category=after.channel.category,
            )
            await member.move_to(newchannel)

        # Delete voice channel
        if (
            before.channel
            and before.channel.name.startswith(
                self.bot.config["voice_channel_creation"]["new_channel_name"]
            )
            and not member.bot
        ):
            if not before.channel.members:
                await before.channel.delete(reason="Channel is empty")


def setup(bot):
    bot.add_cog(TaskCog(bot))
