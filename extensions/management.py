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

    # Listener pour la création des salons vocaux de réunion (et leur supression)
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Création
        try:
            if (
                after.channel.name
                == self.bot.config["voicechannelcreation"]["triggerchannel_name"]
                and not member.bot
            ):
                newchannel = await member.guild.create_voice_channel(
                    self.bot.config["voicechannelcreation"]["newchannel_name"],
                    overwrites=None,
                    category=after.channel.category,
                )
                await member.move_to(newchannel)
        except:
            pass

        # Supression
        try:
            if (
                before.channel.name
                == self.bot.config["voicechannelcreation"]["newchannel_name"]
                and not member.bot
            ):
                if not before.channel.members:
                    await before.channel.delete(reason="Channel is empty")
        except:
            pass


def setup(bot):
    bot.add_cog(TaskCog(bot))
