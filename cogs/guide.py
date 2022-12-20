from unicodedata import name
import discord
import os
from discord.ext import commands
import utils
from utils import embeds
from discord.ext.commands.cooldowns import BucketType
from helpers import checks

class Guide(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(
    name="slimes",
    description="Get the guide for Slimes.",
    )
    @checks.not_blacklisted()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def slimes(self, ctx):
        await ctx.send(embed=embeds.embedSlimes)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def golems(self, ctx):
        await ctx.send(embed=embeds.embedGolems)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def seeker(self, ctx):
        await ctx.send(embed=embeds.embedTS)    

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def warrior(self, ctx):
        await ctx.send(embed=embeds.embedStigWar)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def guard(self, ctx):
        await ctx.send(embed=embeds.embedQG)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def phantom(self, ctx):
        await ctx.send(embed=embeds.embedPhantom)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def avowed(self, ctx):
        await ctx.send(embed=embeds.embedTA)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def lord(self, ctx):
        await ctx.send(embed=embeds.embedStigLord)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def queen(self, ctx):
        await ctx.send(embed=embeds.embedQueen)
        await ctx.send(embed=embeds.embedQueen2)

    
    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def trinityseeker(self, ctx):
        await ctx.send(embed=embeds.embedTS)
    


    @slimes.error
    async def slimes_error(self, ctx, error):
            if isinstance(error, commands.CommandOnCooldown):
                em = discord.Embed(title=f"Command on cooldown!",description=f"Try again in {error.retry_after:.2f}s.",)
                await ctx.send(embed=em)

    @golems.error
    async def golems_error(self, ctx, error):
            if isinstance(error, commands.CommandOnCooldown):
                em = discord.Embed(title=f"Command on cooldown!",description=f"Try again in {error.retry_after:.2f}s.",)
                await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(Guide(bot))