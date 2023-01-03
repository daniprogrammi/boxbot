# this is for twitchIO v2

from twitchio.ext import commands
import shutil
import json

import traceback

from asyncio import Lock

import re

from dotenv import dotenv_values

import os

import sqlite3
from contextlib import closing

# import aiosqlite

envvars = dotenv_values(".env")
data_dir = envvars['DATA_DIR']
        
#alias_dict = {}
#try:
#    with open (os.path.join(data_dir, 'commands.json')) as commandsfile:
#        alias_dict = json.load(commandsfile)
#        commandsfile.close()
#    print(f"loaded {len(alias_dict)} commands. {list(alias_dict.keys())}")
#except (getattr(__builtins__,'FileNotFoundError', IOError)):
#    print('commands file not found! double check your data_dir. creating new commands file...')
#    try:
#        with open(os.path.join(data_dir, 'commands.json'), 'x') as outfile:
#            json.dump(alias_dict, outfile)
#            outfile.close()
#    except Exception as e:
#        print(f"load commands create new commands.json NOPE: {e}")
#except Exception as e:
#    print(f"load commands.json NOPE: {e}")
#    raise(e)

# BLOCKING
# this operation is BLOCKING on module load because the alias_list must exist before the cog is loaded
with closing(sqlite3.connect("commands.db")) as dbconnection:
    with closing(dbconnection.cursor()) as dbcursor:
        dbcursor.row_factory = lambda cursor, row: row[0]
        alias_list = list(set(dbcursor.execute("SELECT * FROM commands").fetchall()))
        print(f"loaded {len(alias_list)} commands. {alias_list}")

class DynCommandsCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        #TODO is anything using this lock anymore?
        self.save_commands_lock = Lock()
        self.dbconnection = sqlite3.connect("commands.db")

    #############
    # migration functions

    @commands.command()
    async def create_commands_database(self, ctx):
        cursor = self.dbconnection.cursor()
        cursor.execute("CREATE TABLE commands (name TEXT, response TEXT, count INTEGER, scheduled INTEGER)")
        self.dbconnection.commit()
        await ctx.send("created!")

    @commands.command()
    async def populate_commands_database(self, ctx):
        for command, data in alias_dict.items():
            cursor = self.dbconnection.cursor()
            command_name = command
            command_response = data['response']
            command_count = data.get('count')
            print(f"{command} {command_response} {command_count}")
            cursor.execute("INSERT INTO commands VALUES (?, ?, ?)", (command_name, command_response, command_count))
        self.dbconnection.commit()
        await ctx.send("created!")

    @commands.command()
    async def print_commands_database(self, ctx):
        cursor = self.dbconnection.cursor()
        rows = cursor.execute("SELECT name, response, count FROM commands").fetchall()
        print(rows)

    ###############

    #def get_save_commands_lock(self):
    #    return self.save_commands_lock

    async def is_extra(ctx):
        return ctx.author.is_mod or ctx.author.name == self.bot.envvars['BOT_ADMIN']

    #def save_commands(self):
    #     try:
    #         shutil.copyfile(os.path.join(data_dir, 'commands.json'), os.path.join(data_dir, 'commands.bak'))
    #         with open(os.path.join(data_dir, 'commands.json'), 'w') as outfile:
    #             json.dump(alias_dict, outfile)
    #             outfile.close()
    #     except Exception as e:
    #         print(f"savecommands NOPE: {e}")

    @commands.command(name='dyn_hello')
    async def dyn_hello(self, ctx: commands.Context):
        await ctx.send(f"Hello2, {ctx.author.name}!")

    #TODO actually handle args here instead of splitting message.content
    #TODO only respect targets with @ otherwise ignore
    @commands.command(aliases=alias_list)
    async def call_response(self, ctx: commands.Context, *args):
        response = ""
        called_command = ctx.message.content.split()[0]
        called_command = called_command[1:].lower()
        called_channel = ctx.channel

        # raw_response = f'{alias_dict[called_command]["response"]}'

        # TODO open readonly?
        # db = sqlite3.connect('file:path/to/database?mode=ro', uri=True)
        with closing(sqlite3.connect("commands.db")) as dbconnection:
            with closing(dbconnection.cursor()) as dbcursor:
                #dbcursor.row_factory = lambda cursor, row: {row[0]: { 'response': row[1], 'count': row[2] } }
                dbcursor.row_factory = sqlite3.Row
                command_dict = dbcursor.execute("SELECT name, response, count FROM commands WHERE name = ?",
                        (called_command,),
                ).fetchone()

                raw_response = f"{command_dict['response']}"

                target = "chat"
                if args:
                    if len(re.findall(r'\w+', ctx.message.content)) > 2:
                        pass
                    else:
                        target = f'{ctx.message.content.split()[1]}'
                        if target.startswith("@"):
                            target = target[1:]
                if "[target]" in command_dict['response']:
                    raw_response = raw_response.replace("[target]", target)
                elif args and target != 'chat':
                    response += f'@{target} '
                # THIS IS SLOPPY. THIS WHOLE THING IS SLOPPY
                if "[attarget]" in command_dict['response']:
                    if target != 'chat':
                        raw_response = raw_response.replace("[attarget]", f"@{target}")
                    else:
                        raw_response = raw_response.replace("[attarget]", f"{target}")
                
                if "[user]" in command_dict['response']:
                    raw_response = raw_response.replace("[user]", ctx.message.author.name)

                if "[count]" in command_dict['response']:
                    newcount = command_dict['count'] + 1
                    dbcursor.execute("UPDATE commands SET count = ? WHERE name = ?",
                            (newcount, called_command)
                            )
                    dbconnection.commit()
                    raw_response = raw_response.replace("[count]", str(newcount))
        
        response += raw_response
        await ctx.send(f'{response}')
        return

    #TODO refactor add and edit into single command with aliases
    @commands.command(name='addcommand')
    async def addcommand(self, ctx: commands.Context, command_name: str, *, command_text: str):
        if ctx.message.echo:
            return
        if not (ctx.author.is_mod or ctx.author.name == self.bot.envvars['BOT_ADMIN']):
            return
        if command_name.startswith(self.bot._prefix):
            command_name = command_name[1:]
        try:
            if command_name in alias_list:
                #TODO handle variable bot command prefix
                await ctx.send(f"command named {command_name} already exists! to change it use !editcommand")
            else:
                command_response = command_text
                command_count = None
                if "[count]" in command_text: command_count = 0
                with closing(sqlite3.connect("commands.db")) as dbconnection:
                    with closing(dbconnection.cursor()) as dbcursor:
                        dbcursor.execute("INSERT into commands VALUES(?, ?, ?, ?, ?)",
                            (command_name, command_response, command_count, None, ctx.channel.name)
                        )
                        dbconnection.commit()
                await ctx.send(f"added command {self.bot._prefix}{command_name}: {command_text}")
                if 'modules.discord' in self.bot._modules.keys():
                    discord_cog = self.bot.get_cog('DiscordCog')
                    discord_bot = discord_cog.discord_bot
                    if 'disco_modules.dyncommands' in discord_bot.extensions:
                        discord_bot.reload_extension('disco_modules.dyncommands')
                # this might be superjanky
                self.bot.unload_module('modules.dyncommands')
                self.bot.load_module('modules.dyncommands')



        except Exception as e:
            print(f'addcommand NOPE: {e}')

    @commands.command(name='editcommand')
    async def editcommand(self, ctx: commands.Context, command_name: str = None, *, command_text: str = None):
        if not (ctx.author.is_mod or ctx.author.name == self.bot.envvars['BOT_ADMIN']):
            return
        #TODO handle variable bot command prefix
        if command_name == None:
            #TODO handle variable bot command prefix
            await ctx.send(f"!editcommand command_name here is the response!")
            return
        if command_name.startswith(self.bot._prefix):
            command_name = command_name[1:]
        with closing(sqlite3.connect("commands.db")) as dbconnection:
            with closing(dbconnection.cursor()) as dbcursor:
                if command_text == None:
                    try:
                        if command_name not in alias_list:
                            await ctx.send(f"I don't have a command named {command_name} or can't edit it from here")
                        else:
                            dbcursor.row_factory = sqlite3.Row
                            command_dict = dbcursor.execute("SELECT name, response, count FROM commands WHERE name = ?",
                                    (command_name,),
                            ).fetchone()
                            #TODO handle variable bot command prefix
                            await ctx.send(f"!{command_name}: {command_dict['response']}")
                        return
                    except Exception as e:
                        print(f"editcommand NOPE: {e}")
                try:
                    command_count = None
                    if "[count]" in command_text: command_count = 0
                    if command_name not in alias_list:
                        dbcursor.execute("INSERT into commands VALUES (?, ?, ?, ?)",
                            (command_name, command_text, command_count, None)
                        )
                        dbconnection.commit()
                        #TODO handle dynamic bot command prefix
                        await ctx.send(f"added command !{command_name}: {command_text}")
                    #TODO elif? how about just else?
                    elif command_name in alias_list:
                        dbcursor.execute("UPDATE commands SET response = ? WHERE name = ?",
                                (command_text, command_name)
                        )
                        dbconnection.commit()
                        #TODO handle dynamic bot command prefix
                        await ctx.send(f"edited command !{command_name}: {command_text}")
                    if 'modules.discord' in self.bot._modules.keys():
                        discord_cog = self.bot.get_cog('DiscordCog')
                        discord_bot = discord_cog.discord_bot
                        if 'disco_modules.dyncommands' in discord_bot.extensions:
                            discord_bot.reload_extension('disco_modules.dyncommands')
                    self.bot.unload_module('modules.dyncommands')
                    self.bot.load_module('modules.dyncommands')
                except Exception as e:
                    print(f"editcommand NOPE: {e}")

    @commands.command(name='delcommand')
    async def delcommand(self, ctx: commands.Context, command_name: str):
        if not (ctx.author.is_mod or ctx.author.name == self.bot.envvars['BOT_ADMIN']):
            return
        if command_name not in alias_list:
            await ctx.send(f"I don't see the command {command_name} to delete...")
            return
        with closing(sqlite3.connect("commands.db")) as dbconnection:
            with closing(dbconnection.cursor()) as dbcursor:
                dbcursor.execute("DELETE FROM commands WHERE name = ?",
                        (command_name,)
                )
                dbconnection.commit()
        await ctx.send(f"deleted {command_name}!")
        self.bot.unload_module('modules.dyncommands')
        self.bot.load_module('modules.dyncommands')

    def cog_unload(self):
        self.dbconnnection.close()

def prepare(bot: commands.Bot):
    # Load our cog with this module...
    bot.add_cog(DynCommandsCog(bot))

def breakdown(bot: commands.Bot):
    # Unload our cog with this module...
    try:
        bot.remove_cog("DynCommandsCog")
    except Exception as e:
        print(e)
