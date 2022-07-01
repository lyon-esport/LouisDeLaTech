from itertools import count

from discord.ext import commands

from les_louisdelatech.utils.discord import is_team_allowed


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
        # Create voice channel block
        if (
            after.channel
            and after.channel.name
            == self.bot.config["voice_channel_creation"]["trigger_channel_name"]
            and not member.bot
        ):
            # List meeting channels already existing in the user's category and order it
            list_channels_name = []

            def predicate(channel):
                return channel.name.startswith(
                    self.bot.config["voice_channel_creation"]["new_channel_name"]
                )

            for channel in filter(predicate, after.channel.category.voice_channels):
                list_channels_name.append(channel.name)

            # Iterate through the existing channels (if they exist) to create an non-existing one
            new_channel_name = None
            channel_number = 1

            while new_channel_name is None:
                channel_name_check = f'{self.bot.config["voice_channel_creation"]["new_channel_name"]} #{channel_number}'
                if (
                    not channel_name_check in list_channels_name
                    or not list_channels_name
                ):
                    new_channel_name = channel_name_check
                channel_number = channel_number + 1

            # Create the channel and move member
            new_channel = await member.guild.create_voice_channel(
                new_channel_name,
                overwrites=None,
                category=after.channel.category,
                bitrate=self.bot.config["voice_channel_creation"]["bitrate"],
            )
            await member.move_to(new_channel)

        # Delete voice channel block
        if (
            before.channel
            and before.channel.name.startswith(
                self.bot.config["voice_channel_creation"]["new_channel_name"]
            )
            and not member.bot
            and not before.channel.members
        ):
            await before.channel.delete(reason="Channel is empty")


def setup(bot):
    bot.add_cog(TaskCog(bot))
