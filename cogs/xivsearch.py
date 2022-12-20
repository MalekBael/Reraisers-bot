from functools import reduce
from random import choice, randint
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
import datetime
import asyncio
import json
import logging
import os
import feedparser
import re
import bs4
from bs4 import BeautifulSoup
import aiohttp
import http
import pyxivapi
import requests
from discord import Embed, File, Member
from discord.ext.commands import Cog, command
from dotenv import load_dotenv
from pyxivapi.models import Filter, Sort
from discord.ext import commands
import csv
import discord

ERROR_COLOR = 0xA11616
DATA_COLOR = 0x0C9C84

def get_token():
    PRIVATE_KEY=os.getenv("XIVSEARCH_TOKEN")
    return(PRIVATE_KEY)

class XIVSearch(Cog):
    def __init__(self, bot):
        self.bot=bot
        self.s = requests.Session()
        self.lodestone_domain = 'na.finalfantasyxiv.com'
        self.lodestone_url = 'http://%s/lodestone' % self.lodestone_domain

    @commands.Cog.listener()
    async def on_ready(self):
        print('XIVSEARCH Loaded')



    @commands.command(name="search", aliases=["xivsearch"], help="Search for an item on the Lodestone.", brief="Search up an item.")
    async def search(self, ctx, *, search):
        SESSION = aiohttp.ClientSession()
        PRIVATE_KEY=get_token()
        CLIENT = pyxivapi.client.XIVAPIClient(api_key=PRIVATE_KEY, session=SESSION)
        results = await CLIENT.index_search(
            name=f"{search}",
            indexes=["Item", "Action", "Trait"],
            columns=["Name", 
            "Icon",
            "Description",
            "ItemKind.Name",
            "ItemUICategory.Name",
            "ClassJobCategory",
            "ActionCategory",
            ],
            language="en",
            string_algo="match",
            page=0,
            per_page=1     
            )
        for each in results['Results']:
            embed = discord.Embed(title=each['Name'], description=f"**{each['ItemUICategory']['Name']}**\n{each['Description']}", colour=DATA_COLOR)
            embed.set_thumbnail(url=f"https://xivapi.com/{each['Icon']}")
            await ctx.send(embed = embed)
            await SESSION.close()


    @commands.command(name="charactersearch", aliases=["csearch", "charsearch"], help="Search for a character on the Lodestone.", brief="Search up a PC.")
    async def character_search(self, ctx, firstName, lastName, server):
        SESSION = aiohttp.ClientSession()
        PRIVATE_KEY=get_token()
        CLIENT = pyxivapi.client.XIVAPIClient(api_key=PRIVATE_KEY, session=SESSION)
        results = await CLIENT.character_search(
            world=f"{server}",
            forename=f"{firstName}",
            surname=f"{lastName}"
            )
        print(results)
        for each in results['Results']:
            characterResults = await CLIENT.character_by_id(
                lodestone_id=f"{each['ID']}",
                extended=True
            )
            embed = Embed(title=f"{characterResults['Character']['Name']}, {characterResults['Character']['Title']['Name']}", description=f"{characterResults['Character']['DC']}, {characterResults['Character']['Server']}", colour=DATA_COLOR)
            embed.add_field(name="Race/Clan",value=f"{characterResults['Character']['Race']['Name']}/{characterResults['Character']['Tribe']['Name']}")
            embed.add_field(name="Nameday", value=characterResults['Character']['Nameday'])
            embed.add_field(name="Guardian Deity", value=characterResults['Character']['GuardianDeity']['Name'])
            embed.add_field(name="Grand Company", value=characterResults['Character']['GrandCompany']['Company']['Name'])
            embed.add_field(name="GC Rank", value=characterResults['Character']['GrandCompany']['Rank']['Name'])
            embed.add_field(name="Free Company", value=characterResults['Character']['FreeCompanyName'])
            embed.add_field(name="Eureka Level",value=characterResults['Character']['ClassJobsElemental']['Level'])
            embed.add_field(name="Bozja Rank",value=characterResults['Character']['ClassJobsBozjan']['Level'])
            embed.add_field(name="Active Class", value=f"{characterResults['Character']['ActiveClassJob']['Job']['Abbreviation']}, Level {characterResults['Character']['ActiveClassJob']['Level']}")
            embed.set_thumbnail(url=characterResults['Character']['Avatar'])
            embed.set_image(url=characterResults['Character']['Portrait'])
            await ctx.send(embed = embed)
            await SESSION.close()

async def setup(bot):
    await bot.add_cog(XIVSearch(bot))