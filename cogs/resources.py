""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 5.3
"""


import discord
import utils
from utils import embeds
import views
from views import views
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


# Here we name the cog and create a new class for the cog.
class Resources(commands.Cog, name="resources"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="resources",
        description="Shows resources for the selected bos",
    )
    # This will only allow non-blacklisted members to execute the command
    @checks.not_blacklisted()
    async def resources(self, context: Context):
        view = views.ResourcesView()
        await context.send("Choose the boss you'd like info on", view=view)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Resources(bot))
