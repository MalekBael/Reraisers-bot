""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 5.3
"""

import discord
from discord.ext import commands
from discord.ext.commands import Context
import utils
from utils import embeds
import views
from views import views
from helpers import checks


class Loadout(commands.Cog, name="holster"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="holster",
        description="Shows the recommended holster of your selected role.",
    )
    @checks.not_blacklisted()
    async def loadout(self, context: Context):
        view = views.HolsterView()
        await context.send('Choose the holster you would like to see', view=view, delete_after=5.0)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Loadout(bot))
