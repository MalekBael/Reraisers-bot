"""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 5.3
"""
import asyncio
import datetime
import json
import os
import platform
import random
import sys
from datetime import datetime as dt

import aiosqlite
import discord
from dateutil import tz
import discord.ext
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from pytz import timezone

import exceptions
from raidbot.database import *
from raidbot.emoji_dict import emoji_dict
from raidbot.event import Event, make_event_from_db
from raidbot.raidbuilder import (JOBS, Character, make_character_from_db,
                                 make_raid)
from utils import embeds

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)



intents = discord.Intents.all()
bot = Bot(command_prefix=commands.when_mentioned_or(
    config["prefix"]), intents=intents)
    #config["prefix"]), intents=intents, help_command=None)


async def init_db():
    async with aiosqlite.connect("database/database.db") as db:
        with open("database/schema.sql") as file:
            await db.executescript(file.read())
        await db.commit()


"""
Create a bot variable to access the config file in cogs so that you don't need to import it every time.

The config is available using the following code:
- bot.config # In this file
- self.bot.config # In cogs
"""
bot.config = config
t = "Etc/GMT+0"
timeZone = tz.gettz(t) if t else tz.tzutc()

@bot.event
async def on_ready() -> None:
    """
    The code in this even is executed when the bot is ready
    """
    setattr(bot, "db", await aiosqlite.connect("database/main.db"))
    print(f"Logged in as {bot.user.name}")
    print(f"discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS Giveaway_Entry (user_id int, message_id int)")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS Giveaway_Running (unique_id int,channel_id int,prize string, hostedby int,total float, running int,entries int,winners int, PRIMARY KEY (unique_id))")
    Giveaway_Updater.start()
    status_task.start()
    if config["sync_commands_globally"]:
        print("Syncing commands globally...")
        await bot.tree.sync()


@tasks.loop(seconds=10)
async def Giveaway_Updater():
    cur = await bot.db.execute("SELECT unique_id,channel_id,prize,hostedby,total,winners FROM Giveaway_Running WHERE running = ?", (1,))
    res = await cur.fetchall()
    if res != None:
        for x in res:
            channel = await bot.fetch_channel(x[1])
            message = await channel.fetch_message(x[0])

            user = await bot.fetch_user(x[3])

            hours, remainder = divmod(int(x[4]-10), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)

            if x[4]-10 <= 0:
                cur = await bot.db.execute("SELECT user_id FROM Giveaway_Entry WHERE message_id = ?", (x[0],))
                res = await cur.fetchall()
                if res:
                    list = []
                    for l in res:
                        y = str(l[0])
                        list.append(y)
                    winners = ""
                    if len(list) < x[5]:
                        for i in range(len(list)):
                            n = random.choice(list)
                            list.remove(n)
                            winner = await bot.fetch_user(int(n))
                            winners += f"{winner.mention}\n"

                    else:
                        for i in range(x[5]):
                            n = random.choice(list)
                            list.remove(n)
                            winner = await bot.fetch_user(int(n))
                            winners += f"{winner.mention}\n"




                    embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: \n{winners}\nHosted by: {user.mention}\n\n♜Ended♜", colour=discord.Colour(0x36393e))
                    await message.edit(content=":piñata:**__Giveaway Ended__**:piñata:",embed=embed)
                    await bot.db.execute("DELETE FROM Giveaway_Running WHERE unique_id = ?", (x[0],))
                    return
                else:
                    embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: Not enough Entries.\nHosted by: {user.mention}\n\n♜Ended♜", colour=discord.Colour(0x36393e))
                    await message.edit(content=":piñata:**__Giveaway Ended__**:piñata:",embed=embed)
                    await bot.db.execute("DELETE FROM Giveaway_Running WHERE unique_id = ?", (x[0],))
                    return

            if x[4]-10 <= 60:
                embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: \TBA/\nHosted by: {user.mention}\n\n♜{seconds}s♜", colour=discord.Colour(0x36393e))
                await message.edit(embed=embed)
            else:


                embed = discord.Embed(description=f"**{x[2]}**\n\nWinner: \TBA/\nHosted by: {user.mention}\n\n♜{days}d:{hours}h:{minutes}m♜", colour=discord.Colour(0x36393e))
                await message.edit(embed=embed)


            await bot.db.execute("UPDATE Giveaway_Running SET total = total - 10 WHERE unique_id = ?", (x[0],))


    await bot.db.commit()



@tasks.loop(minutes=1.0)
async def status_task() -> None:
    """
    Setup the game status task of the bot
    """
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Server Time ' + dt.now().astimezone(timeZone).strftime("%H:%M")))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Server Time ' + dt.now().astimezone(timeZone).strftime("%H:%M")))


@bot.event
async def on_message(message: discord.Message) -> None:
    """
    The code in this event is executed every time someone sends a message, with or without the prefix

    :param message: The message that was sent.
    """
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)


@bot.event
async def on_command_completion(context: Context) -> None:
    """
    The code in this event is executed every time a normal command has been *successfully* executed
    :param context: The context of the command that has been executed.
    """
    full_command_name = context.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    if context.guild is not None:
        print(
            f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})")
    else:
        print(
            f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs")

#region Error

@bot.event
async def on_command_error(context: Context, error) -> None:
    """
    The code in this event is executed every time a normal valid command catches an error
    :param context: The context of the normal command that failed executing.
    :param error: The error that has been faced.
    """
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            title="Hey, please slow down!",
            description=f"You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserBlacklisted):
        """
        The code here will only execute if the error is an instance of 'UserBlacklisted', which can occur when using
        the @checks.not_blacklisted() check in your command, or you can raise the error by yourself.
        """
        embed = discord.Embed(
            title="Error!",
            description="You are blacklisted from using the bot.",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserNotOwner):
        """
        Same as above, just for the @checks.is_owner() check.
        """
        embed = discord.Embed(
            title="Error!",
            description="You are not the owner of the bot!",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Error!",
            description="You are missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to execute this command!",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            # We need to capitalize because the command arguments have no capital letter in the code.
            description=str(error).capitalize(),
            color=0xE02B2B
        )
        await context.send(embed=embed)
    raise error

#endregion Error

#region Cogs
async def load_cogs() -> None:
    """
    The code in this function is executed whenever the bot will start.
    """
    for file in os.listdir(f"./cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")
#endregion Cogs

#region Tickets
#######################################################################################################
@bot.command()
async def tickethelp(ctx):
    with open("data.json") as f:
        data = json.load(f)
    
    valid_user = False

    for role_id in data["verified-roles"]:
        try:
            if ctx.guild.get_role(role_id) in ctx.author.roles:
                valid_user = True
        except:
            pass
    
    if ctx.author.guild_permissions.administrator or valid_user:

        em = discord.Embed(title="Auroris Tickets Help", description="", color=0x00a8ff)
        em.add_field(name="`.new <message>`", value="This creates a new ticket. Add any words after the command if you'd like to send a message when we initially create your ticket.")
        em.add_field(name="`.close`", value="Use this to close a ticket. This command only works in ticket channels.")
        em.add_field(name="`.addaccess <role_id>`", value="This can be used to give a specific role access to all tickets. This command can only be run if you have an admin-level role for this bot.")
        em.add_field(name="`.delaccess <role_id>`", value="This can be used to remove a specific role's access to all tickets. This command can only be run if you have an admin-level role for this bot.")
        em.add_field(name="`.addpingedrole <role_id>`", value="This command adds a role to the list of roles that are pinged when a new ticket is created. This command can only be run if you have an admin-level role for this bot.")
        em.add_field(name="`.delpingedrole <role_id>`", value="This command removes a role from the list of roles that are pinged when a new ticket is created. This command can only be run if you have an admin-level role for this bot.")
        em.add_field(name="`.addadminrole <role_id>`", value="This command gives all users with a specific role access to the admin-level commands for the bot, such as `.addpingedrole` and `.addaccess`. This command can only be run by users who have administrator permissions for the entire server.")
        em.add_field(name="`.deladminrole <role_id>`", value="This command removes access for all users with the specified role to the admin-level commands for the bot, such as `.addpingedrole` and `.addaccess`. This command can only be run by users who have administrator permissions for the entire server.")
        em.set_footer(text="Auroris Development")

        await ctx.send(embed=em)
    
    else:

        em = discord.Embed(title = "Auroris Tickets Help", description ="", color = 0x00a8ff)
        em.add_field(name="`.new <message>`", value="This creates a new ticket. Add any words after the command if you'd like to send a message when we initially create your ticket.")
        em.add_field(name="`.close`", value="Use this to close a ticket. This command only works in ticket channels.")
        #em.set_footer(text="Auroris Development")

        await ctx.send(embed=em)

@bot.command()
async def newticket(ctx, *, args = None):

    await bot.wait_until_ready()

    if args == None:
        message_content = "Please wait, we will be with you shortly!"
    
    else:
        message_content = "".join(args)

    with open("data.json") as f:
        data = json.load(f)

    ticket_number = int(data["ticket-counter"])
    ticket_number += 1
    name = 'Tickets'
    category = discord.utils.get(ctx.guild.categories, name=name)
    ticket_channel = await ctx.guild.create_text_channel(ctx.author.name, category=category)
    #ticket_channel = await ctx.guild.create_text_channel("ticket-{}".format(ticket_number), category=category)
    await ticket_channel.set_permissions(ctx.guild.get_role(ctx.guild.id), send_messages=False, read_messages=False)

    for role_id in data["valid-roles"]:
        role = ctx.guild.get_role(role_id)

        await ticket_channel.set_permissions(role, send_messages=True, read_messages=True, add_reactions=True, embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
    
    await ticket_channel.set_permissions(ctx.author, send_messages=True, read_messages=True, add_reactions=True, embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)

    em = discord.Embed(title="New ticket from {}#{}".format(ctx.author.name, ctx.author.discriminator), description= "{}".format(message_content), color=0x00a8ff)

    await ticket_channel.send(embed=em)

    pinged_msg_content = ""
    non_mentionable_roles = []

    if data["pinged-roles"] != []:

        for role_id in data["pinged-roles"]:
            role = ctx.guild.get_role(role_id)

            pinged_msg_content += role.mention
            pinged_msg_content += " "

            if role.mentionable:
                pass
            else:
                await role.edit(mentionable=True)
                non_mentionable_roles.append(role)
        
        await ticket_channel.send(pinged_msg_content)

        for role in non_mentionable_roles:
            await role.edit(mentionable=False)
    
    data["ticket-channel-ids"].append(ticket_channel.id)

    data["ticket-counter"] = int(ticket_number)
    with open("data.json", 'w') as f:
        json.dump(data, f)
    
    created_em = discord.Embed(title="Tickets", description="Your ticket has been created at {}".format(ticket_channel.mention), color=0x00a8ff)
    
    await ctx.send(embed=created_em, delete_after=180.0)

@bot.command()
async def closeticket(ctx):
    with open('data.json') as f:
        data = json.load(f)

    if ctx.channel.id in data["ticket-channel-ids"]:

        channel_id = ctx.channel.id

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() == "close"

        try:

            em = discord.Embed(title="Auroris Tickets", description="Are you sure you want to close this ticket? Reply with `close` if you are sure.", color=0x00a8ff)
        
            await ctx.send(embed=em)
            await bot.wait_for('message', check=check, timeout=60)
            await ctx.channel.delete()

            index = data["ticket-channel-ids"].index(channel_id)
            del data["ticket-channel-ids"][index]

            with open('data.json', 'w') as f:
                json.dump(data, f)
        
        except asyncio.TimeoutError:
            em = discord.Embed(title="Auroris Tickets", description="You have run out of time to close this ticket. Please run the command again.", color=0x00a8ff)
            await ctx.send(embed=em)

@bot.command()
async def addticketaccess(ctx, role_id=None):

    with open('data.json') as f:
        data = json.load(f)
    
    valid_user = False

    for role_id in data["verified-roles"]:
        try:
            if ctx.guild.get_role(role_id) in ctx.author.roles:
                valid_user = True
        except:
            pass
    
    if valid_user or ctx.author.guild_permissions.administrator:
        role_id = int(role_id)

        if role_id not in data["valid-roles"]:

            try:
                role = ctx.guild.get_role(role_id)

                with open("data.json") as f:
                    data = json.load(f)

                data["valid-roles"].append(role_id)

                with open('data.json', 'w') as f:
                    json.dump(data, f)
                
                em = discord.Embed(title="Auroris Tickets", description="You have successfully added `{}` to the list of roles with access to tickets.".format(role.name), color=0x00a8ff)

                await ctx.send(embed=em)

            except:
                em = discord.Embed(title="Auroris Tickets", description="That isn't a valid role ID. Please try again with a valid role ID.")
                await ctx.send(embed=em)
        
        else:
            em = discord.Embed(title="Auroris Tickets", description="That role already has access to tickets!", color=0x00a8ff)
            await ctx.send(embed=em)
    
    else:
        em = discord.Embed(title="Auroris Tickets", description="Sorry, you don't have permission to run that command.", color=0x00a8ff)
        await ctx.send(embed=em)

@bot.command()
async def deleteticketaccess(ctx, role_id=None):
    with open('data.json') as f:
        data = json.load(f)
    
    valid_user = False

    for role_id in data["verified-roles"]:
        try:
            if ctx.guild.get_role(role_id) in ctx.author.roles:
                valid_user = True
        except:
            pass

    if valid_user or ctx.author.guild_permissions.administrator:

        try:
            role_id = int(role_id)
            role = ctx.guild.get_role(role_id)

            with open("data.json") as f:
                data = json.load(f)

            valid_roles = data["valid-roles"]

            if role_id in valid_roles:
                index = valid_roles.index(role_id)

                del valid_roles[index]

                data["valid-roles"] = valid_roles

                with open('data.json', 'w') as f:
                    json.dump(data, f)

                em = discord.Embed(title="Auroris Tickets", description="You have successfully removed `{}` from the list of roles with access to tickets.".format(role.name), color=0x00a8ff)

                await ctx.send(embed=em)
            
            else:
                
                em = discord.Embed(title="Auroris Tickets", description="That role already doesn't have access to tickets!", color=0x00a8ff)
                await ctx.send(embed=em)

        except:
            em = discord.Embed(title="Auroris Tickets", description="That isn't a valid role ID. Please try again with a valid role ID.")
            await ctx.send(embed=em)
    
    else:
        em = discord.Embed(title="Auroris Tickets", description="Sorry, you don't have permission to run that command.", color=0x00a8ff)
        await ctx.send(embed=em)

@bot.command()
async def addpingedrole(ctx, role_id=None):

    with open('data.json') as f:
        data = json.load(f)
    
    valid_user = False

    for role_id in data["verified-roles"]:
        try:
            if ctx.guild.get_role(role_id) in ctx.author.roles:
                valid_user = True
        except:
            pass
    
    if valid_user or ctx.author.guild_permissions.administrator:

        role_id = int(role_id)

        if role_id not in data["pinged-roles"]:

            try:
                role = ctx.guild.get_role(role_id)

                with open("data.json") as f:
                    data = json.load(f)

                data["pinged-roles"].append(role_id)

                with open('data.json', 'w') as f:
                    json.dump(data, f)

                em = discord.Embed(title="Auroris Tickets", description="You have successfully added `{}` to the list of roles that get pinged when new tickets are created!".format(role.name), color=0x00a8ff)

                await ctx.send(embed=em)

            except:
                em = discord.Embed(title="Auroris Tickets", description="That isn't a valid role ID. Please try again with a valid role ID.")
                await ctx.send(embed=em)
            
        else:
            em = discord.Embed(title="Auroris Tickets", description="That role already receives pings when tickets are created.", color=0x00a8ff)
            await ctx.send(embed=em)
    
    else:
        em = discord.Embed(title="Auroris Tickets", description="Sorry, you don't have permission to run that command.", color=0x00a8ff)
        await ctx.send(embed=em)

@bot.command()
async def deletepingedrole(ctx, role_id=None):

    with open('data.json') as f:
        data = json.load(f)
    
    valid_user = False

    for role_id in data["verified-roles"]:
        try:
            if ctx.guild.get_role(role_id) in ctx.author.roles:
                valid_user = True
        except:
            pass
    
    if valid_user or ctx.author.guild_permissions.administrator:

        try:
            role_id = int(role_id)
            role = ctx.guild.get_role(role_id)

            with open("data.json") as f:
                data = json.load(f)

            pinged_roles = data["pinged-roles"]

            if role_id in pinged_roles:
                index = pinged_roles.index(role_id)

                del pinged_roles[index]

                data["pinged-roles"] = pinged_roles

                with open('data.json', 'w') as f:
                    json.dump(data, f)

                em = discord.Embed(title="Auroris Tickets", description="You have successfully removed `{}` from the list of roles that get pinged when new tickets are created.".format(role.name), color=0x00a8ff)
                await ctx.send(embed=em)
            
            else:
                em = discord.Embed(title="Auroris Tickets", description="That role already isn't getting pinged when new tickets are created!", color=0x00a8ff)
                await ctx.send(embed=em)

        except:
            em = discord.Embed(title="Auroris Tickets", description="That isn't a valid role ID. Please try again with a valid role ID.")
            await ctx.send(embed=em)
    
    else:
        em = discord.Embed(title="Auroris Tickets", description="Sorry, you don't have permission to run that command.", color=0x00a8ff)
        await ctx.send(embed=em)


@bot.command()
async def addadminrole(ctx, role_id=None):

    try:
        role_id = int(role_id)
        role = ctx.guild.get_role(role_id)

        with open("data.json") as f:
            data = json.load(f)

        data["verified-roles"].append(role_id)

        with open('data.json', 'w') as f:
            json.dump(data, f)
        
        em = discord.Embed(title="Auroris Tickets", description="You have successfully added `{}` to the list of roles that can run admin-level commands!".format(role.name), color=0x00a8ff)
        await ctx.send(embed=em)

    except:
        em = discord.Embed(title="Auroris Tickets", description="That isn't a valid role ID. Please try again with a valid role ID.")
        await ctx.send(embed=em)

@bot.command()
async def deladminrole(ctx, role_id=None):
    try:
        role_id = int(role_id)
        role = ctx.guild.get_role(role_id)

        with open("data.json") as f:
            data = json.load(f)

        admin_roles = data["verified-roles"]

        if role_id in admin_roles:
            index = admin_roles.index(role_id)

            del admin_roles[index]

            data["verified-roles"] = admin_roles

            with open('data.json', 'w') as f:
                json.dump(data, f)
            
            em = discord.Embed(title="Auroris Tickets", description="You have successfully removed `{}` from the list of roles that get pinged when new tickets are created.".format(role.name), color=0x00a8ff)

            await ctx.send(embed=em)
        
        else:
            em = discord.Embed(title="Auroris Tickets", description="That role isn't getting pinged when new tickets are created!", color=0x00a8ff)
            await ctx.send(embed=em)

    except:
        em = discord.Embed(title="Auroris Tickets", description="That isn't a valid role ID. Please try again with a valid role ID.")
        await ctx.send(embed=em)



#######################################################################################################
#endregion


#######################################
#RAID BUILDER#
######################################
#region

def job_emoji_str(job_list):
    emoji_str = ""
    for job in job_list:
        if job is not None:
            emoji_str += emoji_dict[job] + " "
    return emoji_str


def role_num_emoji_str(n_tanks, n_healers, n_dps):
    return f"{n_tanks} {emoji_dict['Tank']} {n_healers} {emoji_dict['Healer']} {n_dps} {emoji_dict['DPS']}"


def ping_string(list_of_ids):
    ping_str = "Hey, "
    for i in list_of_ids:
        ping_str += f"<@{i}>, "
    return ping_str[:-2]


def build_countdown_link(timestamp):
    dt_obj = datetime.fromtimestamp(timestamp, tz=timezone("UTC"))
    link = f"https://www.timeanddate.com/countdown/generic?iso={dt_obj.year}{dt_obj.month:02}{dt_obj.day:02}" \
           f"T{dt_obj.hour:02}{dt_obj.minute:02}{dt_obj.second:02}&p0=0&font=cursive"
    return link


@bot.event
async def on_guild_join(guild):
    conn = create_connection(guild.id)
    initialize_db_with_tables(conn)
    conn.close()

@bot.command(name='set-event-channel', help='Sets the channel to post events in. '
                                            'Channel should be given with # and linked. '
                                            'Bot needs to be allowed to post in that channel. '
                                            'Can only be executed by admins.')
@commands.has_permissions(administrator=True)
async def set_event_channel(ctx, channel):
    if channel[0:2] != "<#":
        await ctx.send('Channel should be given with # and linked.')
        return

    channel_obj = bot.get_channel(int(channel[2:-1]))
    if not channel_obj:
        await ctx.send(f'Channel {channel} does not exist.')
        return
    if channel_obj.type.name != 'text':
        await ctx.send(f'Channel {channel} is not a text channel.')

    conn = create_connection(ctx.guild.id)
    if conn is not None:
        db_channel = get_server_info(conn, "event_channel")
        if db_channel:
            update_server_info(conn, "event_channel", channel)
        else:
            create_server_info(conn, "event_channel", channel)
        conn.close()
        await ctx.send(f"Channel {channel} is set as event_channel. All events will now be posted there.")
    else:
        await ctx.send('Could not connect to database.')


def make_event_embed(ev: Event, guild, add_legend=False):
    try:
        creator = guild.get_member(ev.creator_id)
        creator_name = creator.name if creator.nick is None else creator.nick
    except Exception:
        creator_name = "INVALID_MEMBER"
    embed = discord.Embed(title=f"**Event {ev.id}**",
                          description=f"Organized by **{creator_name}**",
                          color=discord.Color.dark_gold())
    embed.add_field(name="**Name**", value=ev.name, inline=False)
    embed.add_field(name="**Time**", value=f"{ev.get_discord_time_format()} -> [Countdown]"
                                           f"({build_countdown_link(ev.timestamp)})", inline=False)
    embed.set_thumbnail(url="https://static.wikia.nocookie.net/finalfantasy/images/a/a3/FFXIV_Quest_Icon.png/revision/latest/scale-to-width-down/174?cb=20210415061951")

    signed_str, bench_str = ev.signed_in_and_benched_as_strs()
    if signed_str:
        embed.add_field(name="**Participants**", value=signed_str, inline=False)
    if bench_str:
        embed.add_field(name="**On the bench**", value=bench_str, inline=False)
    if ev.jobs:
        embed.add_field(name="**Jobs**", value=job_emoji_str(ev.jobs), inline=False)
    else:
        embed.add_field(name="**Required Roles**", value=role_num_emoji_str(*ev.role_numbers), inline=False)

    if add_legend:
        embed.add_field(name="Use reactions to", value=f"{emoji_dict['sign_in']} - sign up"
                                                       f"\n{emoji_dict['bench']} - substitute bench"
                                                       f"\n{emoji_dict['sign_out']} - sign out", inline=False)

    embed.set_footer(text=f"This event is {ev.state}")
    return embed


def make_character_embed(ch: Character, date, num_raids):
    embed = discord.Embed(title=ch.character_name, description=job_emoji_str(ch.jobs),
                          color=discord.Color.dark_gold())
    embed.add_field(name="**Nr. of Events:**", value=str(num_raids), inline=False)
    embed.add_field(name="**Involuntarily benched counter:**", value=str(ch.involuntary_benches),
                    inline=False)
    embed.set_footer(text=f"Registered since {date}")
    return embed


@bot.command(name='show-event', help='Shows an event from the database given its id')
async def show_event(ctx, event_id):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        try:
            event = make_event_from_db(conn, event_id)
            embed = make_event_embed(event, ctx.guild)
            if event.message_link:
                embed.add_field(name="**Original post**", value=f"[link]({event.message_link})", inline=False)
            conn.close()
            await ctx.send(embed=embed)
        except Exception:
            conn.close()
            await ctx.send(f'Could not find event with id {event_id}. This event might not exist (yet).')
    else:
        await ctx.send('Could not connect to database.')


@bot.command(name='show-character', help='Shows characters registered with the given Discord ID')
async def show_character(ctx, discord_id):
    num_id = int(discord_id[3:-1])
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        try:  # TODO: handle multiple characters registered with the same discord id
            chara, date, num_raids = make_character_from_db(conn, num_id, None)
            embed = make_character_embed(chara, date, num_raids)
            conn.close()
            await ctx.send(f"<@{num_id}>'s character:", embed=embed)
        except Exception:
            conn.close()
            await ctx.send(f'Could not find character with id <@{num_id}>. This player might not be registered (yet).')
    else:
        await ctx.send('Could not connect to database.')


@bot.command(name='make-event', help='creates an event given parameters: '
                                     'name date (format d-m-y) time (format HH:MM) '
                                     'num_Tanks num_Heals num_DPS timezone (optional, default UTC)\n'
                                     '**Note:** Parameters are separated by spaces, so if you want a space in'
                                     'for eaxmple <name>, you need to put name in quotation marks like this:'
                                     ' "Event Name"')
async def make_event(ctx, name, date, start_time, num_tanks, num_heals, num_dps, user_timezone="UTC"):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        try:
            tz = timezone(user_timezone)
        except Exception:
            conn.close()
            tz_link = "https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"
            embed = discord.Embed(description=f"A link to all possible timezones can be found [here]({tz_link})",
                                  color=discord.Color.dark_gold())
            await ctx.send(f"Unknown timezone {user_timezone}, use format like 'Europe/Amsterdam'", embed=embed)
            return

        try:
            d, m, y = date.split("-")
            hour, minute = start_time.split(":")
            dt_obj = datetime(int(y), int(m), int(d), int(hour), int(minute))
            dt_obj = tz.normalize(tz.localize(dt_obj))
        except Exception:
            conn.close()
            await ctx.send(f"Could not parse date and/or time, make sure to format like this: "
                           f"dd-mm-yyyy hh:mm (in 24 hour format)")
            return

        event_tup = (name, int(dt_obj.timestamp()), None, None, None,
                     None, f"{num_tanks},{num_heals},{num_dps}",
                     int(ctx.message.author.id), None, "RECRUITING")
        ev_id = create_event(conn, event_tup)

        try:
            event = make_event_from_db(conn, ev_id)
        except Exception:
            conn.close()
            await ctx.send(f'Could not find event with id {ev_id}. This event might not exist (yet).')
            return
        embed = make_event_embed(event, ctx.guild, True)
        # Check if we have an event channel
        db_eventchannel = get_server_info(conn, "event_channel")
        if db_eventchannel:
            channel = db_eventchannel[0][2]
            message = await ctx.guild.get_channel(int(channel[2:-1])).send(embed=embed)
            new_embed = make_event_embed(event, ctx.guild, False)
            new_embed.add_field(name="**Original post**", value=f"[link]({message.jump_url})", inline=False)
            await ctx.send(embed=new_embed)
        else:
            message = await ctx.send(embed=embed)
        update_event(conn, "message_link", message.jump_url, ev_id)
        await message.add_reaction(emoji_dict["sign_in"])
        await message.add_reaction(emoji_dict["bench"])
        await message.add_reaction(emoji_dict["sign_out"])
        conn.close()
        return
    else:
        await ctx.send('Could not connect to database. Need connection to create and save events.')
        return


@bot.command(name='edit-event', help='Edits the given field of an event given its id. Only the event creator can edit. '
                                     'Field can be either name, date, or time. The user_timezone parameter will only '
                                     'matter if the field is "time" and is otherwise ignored.')
async def edit_event(ctx, ev_id, field, value, user_timezone="UTC"):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        db_ev = get_event(conn, ev_id)
        if db_ev:
            event = make_event_from_db(conn, ev_id)
            if event.creator_id != ctx.message.author.id:
                conn.close()
                await ctx.send(f'You are not the author for this event. Only the author can edit events.')
                return
            if field == "name":
                update_event(conn, "name", value, event.id)
                link = event.message_link.split('/')
                message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                    int(link[-1]))
                event.name = value
                embed = make_event_embed(event, message.guild, True if event.state == "RECRUITING" else False)
                await message.edit(embed=embed)
                await ctx.send("Event name updated.")
                conn.close()
                await show_event(ctx, event.id)
                return
            elif field == "date":
                dt_object = datetime.fromtimestamp(event.timestamp)
                try:
                    d, m, y = value.split("-")
                    dt_object = dt_object.replace(day=int(d), month=int(m), year=int(y))
                except Exception:
                    conn.close()
                    await ctx.send(f"Could not parse date, make sure to format like this: "
                                   f"dd-mm-yyyy")
                    return
                timestamp = int(dt_object.timestamp())
                update_event(conn, "timestamp", timestamp, event.id)
                link = event.message_link.split('/')
                message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                    int(link[-1]))
                event.timestamp = timestamp
                embed = make_event_embed(event, message.guild, True if event.state == "RECRUITING" else False)
                await message.edit(embed=embed)
                await ctx.send("Event date updated.")
                conn.close()
                await show_event(ctx, event.id)
                return

            elif field == "time":
                dt_object = datetime.fromtimestamp(event.timestamp)
                try:
                    tz = timezone(user_timezone)
                except Exception:
                    conn.close()
                    tz_link = "https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"
                    embed = discord.Embed(
                        description=f"A link to all possible timezones can be found [here]({tz_link})",
                        color=discord.Color.dark_gold())
                    await ctx.send(f"Unknown timezone {user_timezone}, use format like 'Europe/Amsterdam'", embed=embed)
                    return
                try:
                    hour, minute = value.split(":")
                    dt_object = dt_object.replace(hour=int(hour), minute=int(minute))
                    dt_object = tz.normalize(tz.localize(dt_object))
                except Exception:
                    conn.close()
                    await ctx.send(f"Could not parse time, make sure to format like this: "
                                   f"hh:mm (in 24 hour format)")
                    return
                timestamp = int(dt_object.timestamp())
                update_event(conn, "timestamp", timestamp, event.id)
                link = event.message_link.split('/')
                message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                    int(link[-1]))
                event.timestamp = timestamp
                embed = make_event_embed(event, message.guild, True if event.state == "RECRUITING" else False)
                await message.edit(embed=embed)
                await ctx.send("Event time updated.")
                await show_event(ctx, event.id)
                conn.close()
                return
            else:
                conn.close()
                await ctx.send(f'{field} is not an editable field.\n'
                               f'Editable fields are "name", "date", or "time"')
                return
        else:
            conn.close()
            await ctx.send(f'There is no event with id {ev_id}.')
            return
    else:
        await ctx.send('Could not connect to database.')
        return


@bot.command(name='close-event', help='closes recruitment for an event. Will ask you to decide on the composition'
                                      'via DM. Needs the event ID.\nOptional: Turn off settings the bot uses to help'
                                      'narrow down the search for a *good* raid composition.\nSettings are:\n'
                                      '`maximize_diverse_dps` - if True, the bot will prefer compositions with '
                                      'diverse DPS, i.e. at least one of each type (Melee, Ranged, Caster).\n'
                                      '`use_benched_counter` - if True, the number of times a character was '
                                      '*involuntarily benched* will be counted in his favor.\n'
                                      '`no_double_jobs` - if True, the bot will try to avoid double jobs in the '
                                      'provided compositions. They will still be displayed '
                                      'if they are the only option.\n')
async def close_event(ctx, ev_id, maximize_diverse_dps=True, use_benched_counter=True, no_double_jobs=True):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        db_ev = get_event(conn, ev_id)
        if db_ev:
            event = make_event_from_db(conn, ev_id)
            # Check if we have an event channel
            db_eventchannel = get_server_info(conn, "event_channel")
            if db_eventchannel:
                channel_tag = db_eventchannel[0][2]
                channel = ctx.guild.get_channel(int(channel_tag[2:-1]))
            else:
                channel = ctx
            if event.creator_id != ctx.message.author.id:
                conn.close()
                await ctx.send(f'You are not the author for this event. Only the author can close events.')
                return
            if event.state != "RECRUITING":
                conn.close()
                await ctx.send(f'This event has already been closed.')
                return
            if len(event.participant_ids) < sum(event.role_numbers):
                await ctx.message.author.send(f'There are not enough participants registered for this event. '
                                              f'You can either CANCEL the event, or call on all registered participants '
                                              f'for an UNDERSIZED event in which you fill up with Party Finder. \n'
                                              f'`1` - CANCEL event\n'
                                              f'`2` - UNDERSIZED event\n'
                                              f'`esc` - stop closing dialogue')

                def check(m):
                    return ctx.message.author == m.author \
                           and (m.content == "1" or m.content == "2" or m.content == "esc") \
                           and not m.guild
                # await response
                try:
                    msg = await bot.wait_for('message', check=check, timeout=3600.0)
                except asyncio.TimeoutError:
                    conn.close()
                    await ctx.message.author.send(f'Stopping $close-event dialogue due to timeout.')
                    return
                else:
                    if msg.content == "1":
                        await ctx.message.author.send(f'you have decided to CANCEL the event.')
                        link = event.message_link.split('/')
                        message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                            int(link[-1]))
                        event.state = "CANCELLED"
                        update_event(conn, "state", event.state, event.id)
                        embed = make_event_embed(event, message.guild, False)
                        await message.edit(embed=embed)
                        for em in [emoji_dict["sign_in"], emoji_dict["sign_out"], emoji_dict["bench"]]:
                            await message.remove_reaction(em, bot.user)
                        new_emb = discord.Embed(title=f"**Event {event.id} - {event.name}**",
                                                description=f"Has been **CANCELLED**",
                                                color=discord.Color.dark_gold())
                        await channel.send(embed=new_emb)
                    elif msg.content == "2":
                        await ctx.message.author.send(f'you have decided to run the event UNDERSIZED.')
                        link = event.message_link.split('/')
                        message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                            int(link[-1]))
                        event.state = "UNDERSIZED"
                        update_event(conn, "state", event.state, event.id)
                        # all benched will need to participate
                        for i, _ in enumerate(event.is_bench):
                            event.is_bench[i] = 0
                        update_event(conn, "is_bench", col_str(event.is_bench), event.id)
                        # Jobs need to be figured out on their own, pf can fill anything right?
                        embed = make_event_embed(event, message.guild, False)
                        await message.edit(embed=embed)
                        for em in [emoji_dict["sign_in"], emoji_dict["sign_out"], emoji_dict["bench"]]:
                            await message.remove_reaction(em, bot.user)
                        new_emb = discord.Embed(title=f"**Event {event.id} - {event.name}**",
                                                description=f"will be run **UNDERSIZED**",
                                                color=discord.Color.dark_gold())
                        new_emb.add_field(name="**Time**",
                                          value=f"{event.get_discord_time_format()} -> [Countdown]"
                                                f"({build_countdown_link(event.timestamp)})",
                                          inline=False)
                        signed_str, _ = event.signed_in_and_benched_as_strs()
                        if signed_str:
                            new_emb.add_field(name="**Participants**", value=signed_str, inline=False)
                        await channel.send(ping_string(event.participant_ids), embed=new_emb)
                    elif msg.content == "esc":
                        await ctx.message.author.send(f'Stopping $close-event dialogue.')
                conn.close()
                return
            else:
                # THIS IS WHERE THE MAGIC HAPPENS!
                # Get Information from event
                participants = []
                num_raids = []
                for i, p_id in enumerate(event.participant_ids):
                    chara, _, n_raid = make_character_from_db(conn, p_id, event.participant_names[i])
                    if event.is_bench[i]:
                        chara.benched = True
                    participants.append(chara)
                    num_raids.append(n_raid)

                await ctx.message.author.send(f'Building a group for event {event.id} ...')
                # Get X best raids
                best_raids = make_raid(participants, event.role_numbers[0], event.role_numbers[1], event.role_numbers[2],
                                       no_double_jobs=no_double_jobs,
                                       maximize_diverse_dps=maximize_diverse_dps,
                                       use_benched_counter=use_benched_counter)
                if not best_raids:
                    # No viable combination was found
                    await ctx.message.author.send(f"I could not create a viable group given the participants' jobs and "
                                                  f"the expected roles for this event.")
                    await ctx.message.author.send(f'You can either CANCEL the event, or call on all registered participants '
                                                  f'for a MANUAL event in which you build the party yourself with other jobs or pf. \n'
                                                  f'`1` - CANCEL event\n'
                                                  f'`2` - MANUAL event\n'
                                                  f'`esc` - stop closing dialogue')

                    def check(m):
                        return ctx.message.author == m.author \
                               and (m.content == "1" or m.content == "2" or m.content == "esc") \
                               and not m.guild

                    # await response
                    try:
                        msg = await bot.wait_for('message', check=check, timeout=3600.0)
                    except asyncio.TimeoutError:
                        conn.close()
                        await ctx.message.author.send(f'Stopping $close-event dialogue due to timeout.')
                        return
                    else:
                        if msg.content == "1":
                            await ctx.message.author.send(f'you have decided to CANCEL the event.')
                            link = event.message_link.split('/')
                            message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                                int(link[-1]))
                            event.state = "CANCELLED"
                            update_event(conn, "state", event.state, event.id)
                            embed = make_event_embed(event, message.guild, False)
                            await message.edit(embed=embed)
                            for em in [emoji_dict["sign_in"], emoji_dict["sign_out"], emoji_dict["bench"]]:
                                await message.remove_reaction(em, bot.user)
                            new_emb = discord.Embed(title=f"**Event {event.id} - {event.name}**",
                                                    description=f"Has been **CANCELLED**",
                                                    color=discord.Color.dark_gold())
                            await channel.send(embed=new_emb)
                        elif msg.content == "2":
                            await ctx.message.author.send(f'you have decided to run the event MANUAL.')
                            link = event.message_link.split('/')
                            message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                                int(link[-1]))
                            event.state = "MANUAL"
                            update_event(conn, "state", event.state, event.id)
                            # Jobs need to be figured out on their own, pf can fill anything right?
                            embed = make_event_embed(event, message.guild, False)
                            await message.edit(embed=embed)
                            for em in [emoji_dict["sign_in"], emoji_dict["sign_out"], emoji_dict["bench"]]:
                                await message.remove_reaction(em, bot.user)
                            new_emb = discord.Embed(title=f"**Event {event.id} - {event.name}**",
                                                    description=f"will be run **MANUAL**",
                                                    color=discord.Color.dark_gold())
                            new_emb.add_field(name="**Time**",
                                              value=f"{event.get_discord_time_format()} -> [Countdown]"
                                                    f"({build_countdown_link(event.timestamp)})",
                                              inline=False)
                            signed_str, bench_str = event.signed_in_and_benched_as_strs()
                            if signed_str:
                                new_emb.add_field(name="**Participants**", value=signed_str, inline=False)
                            if bench_str:
                                new_emb.add_field(name="**On the bench**", value=bench_str, inline=False)
                            await channel.send(embed=new_emb)
                        elif msg.content == "esc":
                            await ctx.message.author.send(f'Stopping $close-event dialogue.')
                    conn.close()
                    return

                # We have at least 1 working combo
                combo_str = ""
                for i, (group, comp, score) in enumerate(best_raids):
                    curr_str = ""
                    for player in group:
                        job = comp[group.index(player)]
                        curr_str += f"{emoji_dict[job]} {player.character_name}, "
                    combo_str += f"`{i}` - " + curr_str[:-2] + "\n"

                combo_str += "`rnd` - choose one of the above at random\n" \
                             "`esc` - stop closing dialogue"

                if len(combo_str) >= 2047:
                    # Embed description max length is 2048
                    lines = combo_str.split("\n")
                    msg = ""
                    while len(lines) > 0:
                        curr_line = lines.pop(0)
                        msg += curr_line + "\n"
                        if (len(msg) + len(lines[0]) + 1) >= 2048:
                            new_emb = discord.Embed(title=f"Best Combinations:",
                                                    description=msg,
                                                    color=discord.Color.dark_gold())
                            await ctx.message.author.send("Please choose a composition out of the following:",
                                                          embed=new_emb)
                            msg = ""

                    new_emb = discord.Embed(title=f"Best Combinations:",
                                            description=msg,
                                            color=discord.Color.dark_gold())
                    await ctx.message.author.send("Please choose a composition out of the following:",
                                                  embed=new_emb)

                else:
                    new_emb = discord.Embed(title=f"Best Combinations:",
                                            description=combo_str,
                                            color=discord.Color.dark_gold())
                    await ctx.message.author.send("Please choose a composition out of the following:", embed=new_emb)

                def check(m):
                    return ctx.message.author == m.author \
                           and not m.guild \
                           and (m.content in ["rnd", "esc"] or int(m.content) in range(len(best_raids)))
                # await response
                try:
                    msg = await bot.wait_for('message', check=check, timeout=3600.0)
                except asyncio.TimeoutError:
                    conn.close()
                    await ctx.message.author.send(f'Stopping $close-event dialogue due to timeout.')
                    return
                except Exception:
                    conn.close()
                    await ctx.message.author.send(f'You sent something I cannot convert to a number. '
                                                  f'I cannot deal with this so you will have to '
                                                  f'restart the closing process.')
                    return
                else:
                    if msg.content == "esc":
                        await ctx.message.author.send(f'Stopping $close-event dialogue.')
                        conn.close()
                        return
                    elif msg.content == "rnd":
                        raidnum = random.randint(0, len(best_raids)-1)
                    else:
                        raidnum = int(msg.content)

                    group, comp, score = best_raids[raidnum]
                    # Update bench and jobs
                    for i, player in enumerate(participants):
                        if player in group:
                            event.is_bench[i] = 0
                            job = comp[group.index(player)]
                            event.jobs.append(job)
                            # Players num_raids ++
                            update_player(conn, "num_raids", num_raids[i] + 1,
                                          player.discord_id, player.character_name)
                        else:
                            if event.is_bench[i] == 0:
                                # Player did not want to be benched, involuntary benches ++
                                update_player(conn, "involuntary_benches", player.involuntary_benches + 1,
                                              player.discord_id, player.character_name)

                            event.is_bench[i] = 1
                            event.jobs.append(None)
                    # Sort lists according to FF sorting
                    job_inds = [JOBS.index(j) if j else float('Inf') for j in event.jobs]
                    new_inds = [j[0] for j in sorted(enumerate(job_inds), key=lambda x:x[1])]

                    event.participant_ids = [event.participant_ids[j] for j in new_inds]
                    update_event(conn, "participant_ids", col_str(event.participant_ids), event.id)
                    event.participant_names = [event.participant_names[j] for j in new_inds]
                    update_event(conn, "participant_names", col_str(event.participant_names), event.id)
                    event.jobs = [event.jobs[j] for j in new_inds]
                    update_event(conn, "jobs", col_str(event.jobs), event.id)
                    event.is_bench = [event.is_bench[j] for j in new_inds]
                    update_event(conn, "is_bench", col_str(event.is_bench), event.id)

                    # Edit Event post and make message
                    link = event.message_link.split('/')
                    message = await bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(
                        int(link[-1]))
                    event.state = "COMPLETE"
                    update_event(conn, "state", event.state, event.id)
                    embed = make_event_embed(event, message.guild, False)
                    await message.edit(embed=embed)
                    for em in [emoji_dict["sign_in"], emoji_dict["sign_out"], emoji_dict["bench"]]:
                        await message.remove_reaction(em, bot.user)
                    new_emb = discord.Embed(title=f"**Event {event.id} - {event.name}**",
                                            description=f"Recruitment has ended.",
                                            color=discord.Color.dark_gold())
                    # Get participants with their jobs
                    part_str = ""
                    for j, p_id in enumerate(event.participant_ids):
                        if event.is_bench[j] == 0:
                            part_str += f"{emoji_dict[event.jobs[j]]} {event.participant_names[j]}\n"
                    new_emb.add_field(name="**Participants**", value=part_str, inline=False)
                    # if event.jobs:
                    #     new_emb.add_field(name="**Jobs**", value=job_emoji_str(event.jobs), inline=False)
                    non_benched_ids = [p_id for j, p_id in enumerate(event.participant_ids) if not event.is_bench[j]]
                    await channel.send(ping_string(non_benched_ids), embed=new_emb)
                    conn.close()
                    await ctx.message.author.send(f'You have set the event and participants.')
                    return

        else:
            conn.close()
            await ctx.send(f'There is no event with id {ev_id}.')
            return
    else:
        await ctx.send('Could not connect to database.')
        return


@bot.command(name='register-character', help='Registers a character given parameters: name ("Firstname Lastname") '
                                             'job_list (formatted like "JOB,JOB,JOB", given in order of your priority)\n'
                                             '**Note:** Parameters are separated by spaces, so if you want a space '
                                             'in your name, you need to put name in quotation marks like this:'
                                             ' "Firstname Lastname"\n'
                                             "Example:\n$register-character \"Y'shtola Rhul\" \"THM,CNJ\"")
async def register_character(ctx, name, job_list: str):
    conn = create_connection(ctx.guild.id)
    job_list = job_list.upper()
    if conn is not None:
        disc_id = ctx.message.author.id
        db_chara = get_player_by_id(conn, disc_id)
        if db_chara:
            chara, date, num_raids = make_character_from_db(conn, disc_id, None)
            embed = make_character_embed(chara, date, num_raids)
            conn.close()
            await ctx.send(f"There is already a character registered by <@{disc_id}>, "
                           f"multiple characters are not supported (yet).", embed=embed)
            return
        try:
            chara = Character(disc_id, name, job_list, 0)
            player = (chara.discord_id, name, job_list, datetime.today().strftime('%Y-%m-%d'), 0, 0)
            create_player(conn, player)
            embed = make_character_embed(chara, player[3], player[4])
            await ctx.send(f"<@{chara.discord_id}>'s character:", embed=embed)
        except Exception as e:
            conn.close()
            if e.__str__().__contains__("class"):
                await ctx.send('Please be a responsible Warrior of Light and equip your job/soul stone.')
                return

            await ctx.send('Could not parse name and/or job list. '
                           'Format like this: `$register-character "Firstname Lastname" "JOB,JOB,JOB"`')
            return

    else:
        await ctx.send('Could not connect to database. Need connection to create and save characters.')
        return


@bot.command(name='delete-character', help='Deletes the character registered with your discord id.')
async def delete_character(ctx):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        disc_id = ctx.message.author.id
        db_chara = get_player_by_id(conn, disc_id)
        if db_chara:
            chara, _, _ = make_character_from_db(conn, disc_id, None)
            delete_player(conn, disc_id, chara.character_name)
            conn.close()
            await ctx.send(f'Character **{chara.character_name}** by <@{disc_id}> is now deleted.')
            return
        else:
            conn.close()
            await ctx.send(f'There is no character registered by <@{disc_id}> to delete.')
            return
    else:
        await ctx.send('Could not connect to database. Need connection to delete characters.')
        return


@bot.command(name='add-job', help="adds given job at given position in your character's job list. "
                                  "Pos 0 is in front of 1st job, pos 1 in front of 2nd job etc.")
async def add_job(ctx, job, pos):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        disc_id = ctx.message.author.id
        db_chara = get_player_by_id(conn, disc_id)
        if db_chara:
            chara, date, num_raids = make_character_from_db(conn, disc_id, None)
            job_list = chara.jobs
            try:
                job_list.insert(int(pos), job.upper())
            except Exception:
                conn.close()
                await ctx.send(f'Could not parse position. '
                               f'Position needs to be a valid insertion number for your job list.')
                return
            try:
                chara.set_jobs(job_list)
            except SyntaxError as e:
                conn.close()
                await ctx.send(f'Could not add job. {e.msg}.')
                return
            update_player(conn, "jobs", col_str(chara.jobs), disc_id, chara.character_name)
            embed = make_character_embed(chara, date, num_raids)
            conn.close()
            await ctx.send(f"<@{chara.discord_id}>'s character:", embed=embed)
            return
        else:
            conn.close()
            await ctx.send(f'There is no character registered by <@{disc_id}> to add jobs to.')
            return
    else:
        await ctx.send('Could not connect to database. Need connection to edit characters.')
        return


@bot.command(name='remove-job', help="removes the given job from your character's job list.")
async def remove_job(ctx, job):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        disc_id = ctx.message.author.id
        db_chara = get_player_by_id(conn, disc_id)
        if db_chara:
            chara, date, num_raids = make_character_from_db(conn, disc_id, None)
            try:
                chara.jobs.remove(job.upper())
            except ValueError:
                conn.close()
                await ctx.send(f'Job {job.upper()} is not in your job list.')
                return

            update_player(conn, "jobs", col_str(chara.jobs), disc_id, chara.character_name)
            embed = make_character_embed(chara, date, num_raids)
            conn.close()
            await ctx.send(f"<@{chara.discord_id}>'s character:", embed=embed)
            return
        else:
            conn.close()
            await ctx.send(f'There is no character registered by <@{disc_id}> to remove jobs from.')
            return
    else:
        await ctx.send('Could not connect to database. Need connection to edit characters.')
        return


@bot.command(name='change-character-name', help="change the name attached to the character"
                                                " registered with your discord id.")
async def change_name(ctx, name):
    conn = create_connection(ctx.guild.id)
    if conn is not None:
        disc_id = ctx.message.author.id
        db_chara = get_player_by_id(conn, disc_id)
        if db_chara:
            chara, date, num_raids = make_character_from_db(conn, disc_id, None)
            update_player(conn, "character_name", name, disc_id, chara.character_name)
            chara.character_name = name
            embed = make_character_embed(chara, date, num_raids)
            conn.close()
            await ctx.send(f"<@{chara.discord_id}>'s character:", embed=embed)
            return
        else:
            conn.close()
            await ctx.send(f'There is no character registered by <@{disc_id}>.')
            return
    else:
        await ctx.send('Could not connect to database. Need connection to edit characters.')
        return


@bot.event
async def on_raw_reaction_add(reaction):
    emoji = reaction.emoji
    user = reaction.member
    if user.bot:
        return
    if emoji.name in [emoji_dict['sign_in'].split(":")[1],
                      emoji_dict['bench'].split(":")[1],
                      emoji_dict['sign_out'].split(":")[1]]:
        message = await bot.get_guild(reaction.guild_id).get_channel(reaction.channel_id).fetch_message(reaction.message_id)
        # Find corresponding event
        conn = create_connection(reaction.guild_id)
        if conn is not None:
            db_ev = find_events(conn, "message_link", message.jump_url)
            if not db_ev:
                # Reaction was not on an event post
                conn.close()
                return
            event = Event(*db_ev[0])
            if event.state != "RECRUITING":
                await user.send(f'You are trying to sign in/out for Event {event.id}, '
                                f'but the recruitment has ended.')
                conn.close()
                await message.remove_reaction(emoji, user)
                return

            if user.id in event.participant_ids:
                idx = event.participant_ids.index(user.id)
                if emoji.name == emoji_dict['sign_out'].split(":")[1]:
                    del event.participant_ids[idx]
                    del event.is_bench[idx]
                    del event.participant_names[idx]
                    update_event(conn,  "participant_names", col_str(event.participant_names), event.id)
                    update_event(conn,  "participant_ids", col_str(event.participant_ids), event.id)
                    update_event(conn,  "is_bench", col_str(event.is_bench), event.id)
                    embed = make_event_embed(event, message.guild, True)
                    await message.edit(embed=embed)
                    # await user.send(f'You are now signed out of {event.id}!')
                    conn.close()
                    await message.remove_reaction(emoji, user)
                    return
                elif emoji.name == emoji_dict['bench'].split(":")[1]:
                    if event.is_bench[idx] == 0:
                        # person is not benched and wants to be benched
                        # if it is already 1, person is already benched, nothing happens
                        event.is_bench[idx] = 1
                        update_event(conn, "is_bench", col_str(event.is_bench), event.id)
                        embed = make_event_embed(event, message.guild, True)
                        await message.edit(embed=embed)
                        conn.close()
                        await message.remove_reaction(emoji, user)
                        return
                elif emoji.name == emoji_dict['sign_in'].split(":")[1]:
                    if event.is_bench[idx] == 1:
                        # person is benched and wants to be signed up normally
                        # if it is already 0, person is already signed up, nothing happens
                        event.is_bench[idx] = 0
                        update_event(conn, "is_bench", col_str(event.is_bench), event.id)
                        embed = make_event_embed(event, message.guild, True)
                        await message.edit(embed=embed)
                        conn.close()
                        await message.remove_reaction(emoji, user)
                        return
            else:
                # user not in list yet
                if not emoji.name == emoji_dict['sign_out'].split(":")[1]:  # if they aren't signed in, "sign_out" will not do anything
                    db_player = get_player_by_id(conn, user.id)
                    if not db_player:
                        # user also not in db
                        await user.send(f'You are trying to sign in to Event {event.id}, '
                                        f'but you are not registered yet! '
                                        f'Please register with $register-character on your server')
                        conn.close()
                        await message.remove_reaction(emoji, user)
                        return
                    chara, _, _ = make_character_from_db(conn, user.id, None)
                    if emoji.name == emoji_dict['sign_in'].split(":")[1]:
                        bench = 0
                    else:
                        bench = 1
                    event.participant_names.append(chara.character_name)
                    event.participant_ids.append(chara.discord_id)
                    event.is_bench.append(bench)
                    update_event(conn, "participant_names", col_str(event.participant_names), event.id)
                    update_event(conn, "participant_ids", col_str(event.participant_ids), event.id)
                    update_event(conn, "is_bench", col_str(event.is_bench), event.id)
                    embed = make_event_embed(event, message.guild, True)
                    await message.edit(embed=embed)
                    # await user.send(f'You are now signed in for {event.id}!')
                    conn.close()
                    await message.remove_reaction(emoji, user)
                    return

            # await user.send(f'You are trying to sign in to Event {event.id}!')
            conn.close()
            await message.remove_reaction(emoji, user)
            return
        else:
            await message.remove_reaction(emoji, user)
            await user.send('Could not connect to database to process you signing in. '
                            'Please contact an admin for this bot.')
            return
    else:
        return


#endregion


asyncio.run(init_db())
asyncio.run(load_cogs())
bot.run(os.getenv("DISCORD_TOKEN"))