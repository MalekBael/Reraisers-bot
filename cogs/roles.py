from __future__ import annotations
import os
from dotenv import load_dotenv
from os import environ as env
from typing import TYPE_CHECKING
import discord
from discord import Interaction, Member, Object, SelectOption
from discord.ext.commands import Cog
from discord.ui import Select, View
from discord.utils import get
from discord.ext import commands
from discord.ext.commands import Context

if TYPE_CHECKING:
    from discord.abc import Snowflake

ASSIGNABLE_ROLE_IDS = 1007375667182182482,1007082257774825556,1042068038377287700,1042066957358342286,1042067505335762994,1042066576435855461,1042066781273075802,1042067357071315076,1042066833609597140,1042066925766848522


class RolesView(View):
    def __init__(self, *, member: Member):
        super().__init__(timeout=None)

        self.add_item(RolesSelect(member=member))


class RolesSelect(Select["RolesView"]):
    def __init__(self, *, member: Member):
        super().__init__(
            placeholder="Select your new roles",
            min_values=0,
            max_values=len(ASSIGNABLE_ROLE_IDS),
            options=[
                SelectOption(
                    label=member.guild.get_role(role_id).name,  # type: ignore
                    value=str(role_id),
                    default=member.get_role(role_id) is not None,
                )
                for role_id in ASSIGNABLE_ROLE_IDS
            ],
        )

    async def callback(self, interaction: Interaction):
        assert isinstance(interaction.user, Member)

        roles: list[Snowflake] = interaction.user.roles  # type: ignore
        # since list is invariant, it cannot be a union
        # but apparently Role does not implement Snowflake, this may need a fix

        for role_id in ASSIGNABLE_ROLE_IDS:
            if (
                interaction.user.get_role(role_id) is None
                and str(role_id) in self.values
            ):
                # user does not have the role but wants it
                roles.append(Object(role_id))
                option = get(self.options, value=str(role_id))
                if option is not None:
                    option.default = True
            elif (
                interaction.user.get_role(role_id) is not None
                and str(role_id) not in self.values
            ):
                # user has the role but does not want it
                role_ids = [r.id for r in roles]
                roles.pop(role_ids.index(role_id))
                option = get(self.options, value=str(role_id))
                if option is not None:
                    option.default = False

        await interaction.user.edit(roles=roles)
        await interaction.response.defer()

        new_roles = [
            interaction.guild.get_role(int(value)).name  # type: ignore
            for value in self.values
        ]

        await interaction.message.edit(
            content=f"You now have {', '.join(new_roles) or 'no roles'}", view=self.view
        )

class Roles(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roles", description="select a role",)
    async def roles(self, context : Context):
        view = RolesView(member=context.author)
        embed = discord.Embed(title="Roles", description="Choose your new roles, after selecting the roles, click outside of the menu to apply. the menu will dissapear after 20 seconds")
        embed.set_image(url="https://media.discordapp.net/attachments/892023575245103104/1010334826894733322/banner.png")
        await context.send(embed=embed, delete_after=20.0)
        await context.send(view=view, delete_after=20.0)
        await context.message.delete()

async def setup(bot):
    await bot.add_cog(Roles(bot))