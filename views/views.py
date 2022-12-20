from os import environ as env

import discord
import utils
from utils import embeds
from discord.ui import Select, View
from discord.utils import get
from discord import Interaction, Member, Object, SelectOption


class Holster(discord.ui.Select):
    def __init__(self):
        selectOptions = [
            discord.SelectOption(label="Tank", description="GNB/PLD/WAR/DRK"),
            discord.SelectOption(label="Healer", description="WHM/AST/SCH/SGE"),
            discord.SelectOption(label="Melee", description="DRG/NIN/SAM/MNK/RPR"),
            discord.SelectOption(label="Caster", description="BLM/RDM/SMN"),
            discord.SelectOption(label="Ranged", description="BRD/MCH/DNC"),
        ]
        super().__init__(placeholder='Select your role', min_values=1, max_values=1, options=selectOptions)
    

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Tank':
            return await interaction.response.send_message(embed=embeds.embedTank, ephemeral=True)
        if self.values[0] == 'Healer':
            return await interaction.response.send_message(embed=embeds.embedHealer, ephemeral=True)
        if self.values[0] == 'Melee':
            return await interaction.response.send_message(embed=embeds.embedMelee, ephemeral=True)
        if self.values[0] == 'Caster':
            return await interaction.response.send_message(embed=embeds.embedCaster, ephemeral=True)
        if self.values[0] == 'Ranged':            
            return await interaction.response.send_message(embed=embeds.embedRanged, ephemeral=True)
        await interaction.response.send_message(f'you chose {self.values[0]}', ephemeral=True)

class HolsterView(discord.ui.View):
    def __init__(self, *, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(Holster())

class Resources(discord.ui.Select):
    def __init__(self):
        selectOptions = [
            discord.SelectOption(label="Slimes"),
            discord.SelectOption(label="Golems"),
            discord.SelectOption(label="Trinity Seeker"),
            discord.SelectOption(label="Dahu"),
            discord.SelectOption(label="Stigymoloch Warrior"),
            discord.SelectOption(label="Queen's Guard"),
            discord.SelectOption(label="Bozjan Phantom"),
            discord.SelectOption(label="Trinity Avowed"),
            discord.SelectOption(label="Stigymoloch Lord"),
            discord.SelectOption(label="The Queen"),
        ]
        super().__init__(placeholder="Select the boss you'd like info on", min_values=1, max_values=1, options=selectOptions)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Slimes':
            return await interaction.response.send_message(embed=embeds.embedSlimes, ephemeral=True)
        if self.values[0] == 'Golems':
            return await interaction.response.send_message(embed=embeds.embedGolems, ephemeral=True)
        if self.values[0] == 'Trinity Seeker':
            return await interaction.response.send_message(embed=embeds.embedTA, ephemeral=True)
        if self.values[0] == 'Dahu':
            return await interaction.response.send_message(embed=embeds.embedDahu, ephemeral=True)
        if self.values[0] == 'Stigymoloch Warrior':            
            return await interaction.response.send_message(embed=embeds.embedStigWar, ephemeral=True)
        if self.values[0] == "Queen's Guard":
            return await interaction.response.send_message(embed=embeds.embedQG, ephemeral=True)
        if self.values[0] == 'Bozjan Phantom':
            return await interaction.response.send_message(embed=embeds.embedPhantom, ephemeral=True)
        if self.values[0] == 'Trinity Avowed':            
            return await interaction.response.send_message(embed=embeds.embedTA, ephemeral=True)
        if self.values[0] == 'Stigymoloch Lord':            
            return await interaction.response.send_message(embed=embeds.embedStigLord, ephemeral=True)
        if self.values[0] == 'The Queen':            
            return await interaction.response.send_message(embed=embeds.embedQueen, ephemeral=True)
        await interaction.response.send_message(f'you chose {self.values[0]}', ephemeral=True)

class ResourcesView(discord.ui.View):
    def __init__(self, *, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(Resources())