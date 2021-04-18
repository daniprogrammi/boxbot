import socket
import os, sys, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath('.'))))
import subprocess
import pathlib
from pathlib import Path
from virtual_controllers.vserver import VServer as vs
from virtual_controllers import vclient
import twitchio
from twitchio.ext import commands
from ansimarkup import ansiprint as print
import urllib
import asyncio
from virtual_controllers import vkeyboard as vk
import simpleobsws
import random
import glob
import json
import time
from controller_to_obs import TwitchController
import functools
from chatters import Users

# TODO:
#   user profiles --- info given by viewers that can be queried by everyone
#   each user should be able to set their attributes and set the privacy of the attr
#   e.g. !stupac62.pronouns ; return "WAP"
#        !KingTitan_Atlas.followage ;
#        nickname/timezone/city/blah
#   user specific commands
#####   refactoring never ends
#####   Sound alerts
#####   random browser source; specify filters for known/expected links
#       ---> like a certain standard for cropping clips from twitch or youtube etc
#####     Timers/Event Listeners
##### Grabbing clips from other users (for use in !so command)
#"""
#https://github.com/Teekeks/pyTwitchAPI https://pytwitchapi.readthedocs.io/en/latest/modules/twitchAPI.twitch.html#module-twitchAPI.twitch
#get_clips(broadcaster_id: Optional[str] = None, game_id: Optional[str] = None
#"""
# general argparse for chat commands
# migrate nightbot commands and streamlabs commands(if any)
#### (ask begin) send commands from nvim to the chat/to privatechat maybbbbb
#
#


IN_THE_BOX = [
        "struggle!",
        " an even smaller box",
        "cookies",
        "Actually, it's empty",
        "a head!",
        "chocolates",
        "Chonky Ryan Gosling",
        ":)",
        "*screams*",
        {"!shibaheart": "A SHIBA PUPPY"},
        ]

IN_THE_BOX_TEST = [
        {"!shibaheart": "A SHIBA PUPPY"},
        {"!ss_test": "A test of the switcher!!"},
        ]

OBS_RANDOM_MEDIA_ROOT = (
        "/mnt/c/Users/Dani/Documents/Twitch/OBS_Scene_Switch_Assets/gifs/"
        )



def missing_env_var(var_name):
    raise ValueError(
            (
                f"Please populate the {var_name} environment variable to run the bot. "
                "See README for more details."
                )
            )

## Get the value for this here: https://twitchapps.com/tmi/
if "TWITCH_OAUTH_TOKEN" not in os.environ:
    missing_env_var("TWITCH_OAUTH_TOKEN")

if "BOT_NAME" not in os.environ:
    missing_env_var("BOT_NAME")

if "CHANNEL" not in os.environ:
    missing_env_var("CHANNEL")

TOKEN = os.environ["TWITCH_OAUTH_TOKEN"]
BOT_NAME = os.environ["BOT_NAME"]
CHANNEL = os.environ["CHANNEL"]
GAMEPORT = os.environ["GAMEPORT"]
ENCODING = "utf-8"

##
class Bot(commands.Bot):
    # Bot's internal methods
    def __init__(self):
        super().__init__(
                irc_token=TOKEN,
                client_id="adbcgdfja",
                nick=BOT_NAME,
                prefix="!",
                initial_channels=[CHANNEL],
                )
        self.bot_uptime = time.time()
        self.requests = {'count': 0}

        self.fight_client = None
        self.player1 = None
        self.player2 = None

    async def initialize_obsws(self, ctx):
        print(f"initializing obs with loop: {self.loop}")
        self.obs_ws = simpleobsws.obsws(
                host=os.environ["HOSTNAME"],
                port=os.environ["PORT"],
                password=os.environ["PASSWORD"]
                #loop=self.loop
                )
        #self.loop.create_task(self.obs_ws.connect())
        await self.obs_ws.connect()
        return

    async def event_ready(self):
        print(f"Ready | {self.nick}")
        await self.initialize_obsws(None)
        await self.twitch_controller()

    async def event_message(self, message):
        print(f"#{message.author.name}: {message.content}")
        # check if it's a message that is a username

        username = message.content.split()[0].lstrip("!").lower()
        username = username.split('.')[0]
        # anyone requesting a specific attr
        # anyone requesting basic info
        # the user themselves setting their info !girlwithbox.location NYC
        if Users('girlwithbox').check_db_for_user(username) or username == message.author.name.lower():
            if username == message.author.name.lower() and len(message.content.split()) > 1:
                # The user is themself and they want to set some info
                await self.user_setter(message)
            elif '.' in message.content:
                # requesting an attr
                await self.get_attr(message)
            if len(message.content.split()) == 1 and len(message.content.split('.')) == 1:
                # TODO: getter
                await self.user_getter_all(message)

        await self.handle_commands(message)
        return

    # TODO: timers

    # TODO: Event Listeners
    async def on_streaming(self, data):
        stream_start_time = time.time()
        return

    async def on_event(self, data):
        print(f"New event: Type: {type(data)} | Raw Data: {data}")
        return

    async def on_switchscenes(self, data):
        print(f'Scene switched to "{data}, {data}"')  # ['scene-name'] ['sources']


    def is_owner(ctx):
        return ctx.author.display_name == "girlwithbox"

    def is_mod(ctx):
        return ctx.author.is_mod

    def is_sub(ctx):
        return ctx.author.is_subscriber

    # TODO:
    def is_vip(ctx):
        return

    ############################################################################
    #                        OBS Commands/ Helpers                                  #
    ############################################################################

    async def make_request(self, request, data, verbose=False):
        if data:
            result = await self.loop.create_task(self.obs_ws.call(request, data))
        else:
            result = await self.loop.create_task(self.obs_ws.call(request)) # Does this need to be create_task
            # Make a request with the given data
        if verbose:
            print("Request returned: ", result)
        return result

    async def toggle_src(self, sourceName, sceneName=None):
        # Get source property, check if render is True if it is set render to false, else true
        data = {"item": sourceName}
        request = "GetSceneItemProperties"
        result = await self.make_request(request, data)
        print(f"Current scene item settings from result: ", result)

        curr_visibility = result["visible"]
        data = {"sourceName": sourceName, "sourceSettings": {"render": True}}
        result = await self.make_request("SetSourceSettings", data)
        print(f"Render set to true {result}")
#        try: # TODO: get render
#            render = result["sourceSettings"]["render"]
#        except KeyError:
#            render = False
        new_visibility = not curr_visibility
        if not sceneName:
            data = {"item": sourceName, "visible": new_visibility}

        request = "SetSceneItemProperties"
        result = await self.make_request(request, data)
        return

    async def get_current_scene_items(self):
        request = "GetCurrentScene"
        sceneName = await self.make_request(request, None)
        scene_item_list = sceneName['sources']
        return scene_item_list

    async def move_scene_item(self, sourceName, new_x, new_y):
        request = "SetSceneItemProperties"
        data = {"item": sourceName, "position": {"x":new_x, "y":new_y}}
        result = await self.make_request(request, data)
        return

    async def twitch_controller(self):
        controller = TwitchController()
        # TODO: obs-websocket protocol ahead of simpleobsws
        current_scene_items = await self.get_current_scene_items()
        current_scene_items = [{'name':item['name'], 'x':item['x'], 'y':item['y']} for item in current_scene_items if item['render'] is True]
        # move index when joystick is hit
        sourceName = None

        vals_generator = controller.joystick_source()

        scene_item_index = 0
        async for vals in vals_generator:
            # TODO: Add/Subtract from original position
            # Numpy, batch requests
            if vals[2]:
                scene_item_index += 1
                if scene_item_index >= len(current_scene_items):
                    scene_item_index = 0
            if sourceName is None or sourceName != current_scene_items[scene_item_index]['name']:
                currentScene = current_scene_items[scene_item_index]
                sourceName = currentScene['name']
                print(f"Switched to {sourceName}, {currentScene}")

            origin_x, origin_y = currentScene['x'], currentScene['y']

            await self.move_scene_item(sourceName, vals[0], vals[1])

        return

    async def set_browser_src(self, sourceName, newurl):
        request = "SetSourceSettings"
        data = {"sourceName": sourceName, "sourceSettings": {"url": newurl}}
        result = await self.make_request(request, data)
        return


    ############################################################################
    #                         Twitch Commands                                  #
    ############################################################################

    @commands.command(name='bot_uptime')
    async def bot_uptime(self, ctx):
        await ctx.send(f"{round((time.time() - self.bot_uptime)/60, 2)} minutes since bot last broke")
        return

    @commands.check(is_mod)
    @commands.command(name='set_visible')
    async def set_visible(self, ctx=None, sceneItem=None, boolean=True):
        if ctx:
            sceneItem = ctx.message.content.split()[1:]
            if len(sceneItem) > 1: # Scene item and bool passed as arg
                sceneItem, boolean = sceneItem[0], sceneItem[1]
            else:
                sceneItem = sceneItem[0]
            print(sceneItem, boolean)
        request = "SetSceneItemProperties"
        result = await self.make_request(request, {'item': sceneItem, 'visible': boolean})
        return

    @commands.command(name="get_position")
    async def get_src_position(self, ctx):
        content = ctx.message.content.split()
        sourceName = content[1]
        data = {"item":sourceName}

        result = await self.make_request("GetSceneItemProperties", data)

        print(f"type:{type(result)}, result:{(result)}")
        await ctx.send(f"x:{result['position']['x']}, y:{result['position']['y']}")
        return

    @commands.check(is_mod)
    @commands.command(name="vserver")
    async def vserver_start(self, ctx):
        server_env = vs.getsubprocessenv()

        start_server_file = os.path.join(os.path.abspath('.'), 'start_server.ps1')
        if not os.path.isfile(start_server_file):
           with open(start_server_file, 'w') as f:
               f.write(f"$env:GAMEPORT='{GAMEPORT}'\n")
               f.write("cd C:\\Users\\Dani\\Documents\\Twitch\\Coding\\virtual_controllers\\\n")
               f.write(f"python vserver.py {GAMEPORT}")

        #TODO: use pathlib to build start_server_script path
        #start_server_file = Path.cwd().joinpath(Path('start_server.ps1'))
        #start_server_cmd = ["powershell.exe", "-File",
        #        r"C:\Users\Dani\Documents\Twitch\Coding\twitch_chatbot\twitch_chatbot\start_server.ps1"]
        #start_server_cmd_str = f"{start_server_cmd[0]} {start_server_cmd[1]} {start_server_cmd[2]}"
        #proc = subprocess.Popen(start_server_cmd)
        #proc = await asyncio.create_subprocess_shell(start_server_cmd_str, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        #stdout, stderr = await proc.communicate()
        #if proc.returncode == 0:
        #    await ctx.send("Fight Server started! SeemsGood")
        #else:
#            print(f'Exited with {proc.returncode}')
#            if stdout:
#                print(f'[stdout]: \n{stdout.decode()}')
#            if stderr:
#                print(f'[stderr]:\n{stderr.decode()}')
#

        self.fight_client = vclient.VClient(os.environ['HOSTNAME'], int(GAMEPORT))
        # TODO: Try passing the loop also
        loop = asyncio.get_running_loop()
        self.fight_client.start_client(loop)
        await ctx.send("Fight Client (MAYBE) started! SeemsGood")

        return

    @commands.check(is_mod)
    @commands.command(name="vclose")
    async def vclose(self):
       # Close client server
       self.fight_client.close()
       return

    @commands.check(is_mod)
    @commands.command(name="player1")
    async def assign_player1(self, ctx, keyb=None):
        if not self.player1:
            content = ctx.message.content.split()
            playername = content[1].lower()

            request = { 'request': 'create_player', 'player': playername }
            self.player1 = playername
            self.fight_client.send(request)
            await ctx.send(f"Set Player 1 as {self.player1}")
        else:
            await ctx.send("Player 1 already assigned!!")

        return

    @commands.check(is_mod)
    @commands.command(name="player2")
    async def assign_player2(self, ctx):
        if not self.player2:
            content = ctx.message.content.split()
            playername = content[1].lower()

            request = { 'request': 'create_player', 'player': playername }
            self.player2 = playername
            self.fight_client.send(request)
            await ctx.send(f"Set Player 2 as {self.player1}")
        else:
            await ctx.send("Player 2 already assigned!!")
        return
    
    @commands.check(is_mod)
    @commands.command(name="chplayer")
    async def chplayer(self, ctx):
        # !chplayer player1 new_name
        old_player, new_player = ctx.message.content.split()[1:]
        if self.player1 or self.player2:
            request = { 'request': 'overwrite_player', 'old_player': old_player.lower(), 'new_player': new_player.lower() }
            self.fight_client.send(request)
            await ctx.send(f"Changed {old_player} to {new_player}")
        else:
            await ctx.send("No players set")
        return


    def is_player(self, ctx):
        name = ctx.author.display_name.lower()
        return name == self.player1 or name == self.player2

    # TODO: make character select

    #@commands.check(is_player)
    @commands.command(name='fight')
    async def fight(self, ctx):
        name = ctx.author.display_name.lower()
        if name == self.player1 or name == self.player2:
            pass
        else:
            ctx.send("Not your turn bru")
            return
        content = ctx.message.content.split()

        request = {'request': 'play'}
        if ctx.author.display_name.lower() == self.player1:
            player = self.player1
            request['player'] = 'player1'
        elif ctx.author.display_name.lower() == self.player2:
            player = self.player2
            request['player'] = 'player2'
        else:
            ctx.send("Not your turn!!")

        request['moveset'] = content[1][:100] if len(content[1]) > 100 else content[1]
        print("Moveset:", request['moveset'])
        self.fight_client.send(request)
        return

    # If args passed in then this is a "setter" command
    #   if setter it must be set by the user themselves (or a mod)
    # Else it's a getter command
    #   if it contains '.', we're getting a specific attr
    #   if not return a basic set of attrs -- name, pronouns, <random>
    # TODO:x try name is twitchio.dataclass.User
    #      x read into module and figure out a workaround
    #      ✓ or create my own decorator
    # TODO Create my own decorator in the User class which checks if the
    #       command string is a username and then sets, may call Twitchio.command directly afterwards

    def _is_command_username(message):

        message_args = message.content.split()

        if len(msg_split := message_args[0].split('.')) > 1:
            username = msg_split[0]
            attr = msg_split[1]
            arg = message_args[1]
        else:
            username = message_args[0].split('.')[0]

        if username == ctx.message.author.display_name:
            return user_setter
            # Get user info
            # Someone who is not the user themselves wants to see their info
        else:
            return ctx.send("Invalid call for the moment")

    async def user_setter(self, message):
        # TODO: check if user is in db, load existing user_obj if so,
        # else create user obj and set attr
        # !girlwithbox.attrname arg
        content = message.content.split('.')
        if len(content) > 2:
            arg = " ".join(content[2:])
            attr = content[1]
        elif len(content) == 2:
            attr, arg = content[1].split()
        else:
            return ctx.send("Sorry, we're not doing that right now")

        username = message.author.display_name
        user = Users(username)
        user.set(attr, arg)

        await message.channel.send("Saved your info! SeemsGood")
        return

    async def get_attr(self, message):
        username, attr = message.content.split('.')
        user = Users(username)
        await message.channel.send(f"{attr}: {user.attributes[attr]}")
        return

    async def user_getter_all(self, message):
        username = message.content.strip('!')
        attr = Users(username).attributes
        await message.channel.send(f"""For user {username}, pronouns: {attr['pronouns']},
                location: {attr['location']}, club penguin: {attr['club_penguin']}""")
        return


        #!girlwithbox
        # <Initializes all of the stuff if this is their first call to that user command>
        # < or returns some basic info if there's already some values in there >
        #!girlwithbox.name
        #> "Dani"
    @commands.command(name="welcome")
    async def welcome(self, ctx):
        await ctx.send("Welcome in raiders peepoHey. I'm the girl! This channel has been super programming focused recently"
                "but sometimes I play games here too! The vibe is chaotic casual, "
                "drinks are in the back and we hope you enjoy your stay peepoHey")
        return

    @commands.command(name="sub")
    async def sub(self, ctx):
        await ctx.send("I appreciate everyone who subs, but it's definitely better spent on donations.")
        await ctx.send("!aapi")
        return

    @commands.command(name="aapi")
    async def aapi(self, ctx):
        await ctx.send("Here are some links to resources, info and places to donate"
                " to help stop anti-Asian violence https://anti-asianviolenceresources.carrd.co/")
        return

    @commands.command(name="blm")
    async def blm(self, ctx):
        await ctx.send("Here are some links to resources, info and donation links to support"
                " Black Lives Matter https://blacklivesmatters.carrd.co/")
        return

    @commands.command(name="face")
    async def face(self, ctx):
        await ctx.send("Here's what happened... https://clips.twitch.tv/BlithePatientHedgehogSoonerLater-H7myyAeGy7iHig2w")
        return

    @commands.command(name="project")
    async def project(self, ctx):
        await ctx.send("Can we get chat to play Mortal Kombat? Creating a client to send chat input to steam ")
        return

    @commands.command(name="discord")
    async def discord(self, ctx):
        await ctx.send("Join my discord! [Put pressure on me to maintain it] https://discord.gg/4RXASvcG6k")
        return

    @commands.command(name="twitter")
    async def twitter(self, ctx):
        await ctx.send("DxCat For more box-related shenanigans follow me on twitter www.twitter.com/girlwithbox DxCat")
        return

    @commands.command(name="github")
    async def github(self, ctx):
        await ctx.send("Find my code on GitHub! https://github.com/Danicodes")
        return

    # Events don't need decorators when subclassed
    @commands.command(name="role")
    async def role(self, ctx):
        owner = Bot.is_owner(ctx)
        mod = Bot.is_mod(ctx)
        if owner:
            await ctx.send(f"{ctx.author.name} is the channel owner")
        elif mod:
            await ctx.send(f"{ctx.author.name} is a channel mod")
        else:
            await ctx.send(f"no roles found for {ctx.author.name}")
        return

    @commands.check(is_owner)
    @commands.command(name="cam_refresh")
    async def cam_refresh(self, ctx):
        request = "SetSourceSettings"
        print("Shutting off cam")
        await self.make_request(request, {'sourceName':"HDWebcam", 'sourceSettings': {'active': False}})
        print("Turning Camera Back On")
        result = await self.make_request(request, {'sourceName':"HDWebcam", 'sourceSettings': {'active': True}})
        print(result)
        # await ctx.send("No, stop it")
        return

    @commands.command(name="box")
    async def box_command(self, ctx):
        # TODO: file mapping text to media; might need class for items
        choice = random.choice(IN_THE_BOX)
        # parse_choice if it is chat_cmd
        message_set = ["What's in the box?"]

        if type(choice) is dict:
            message_set.extend(
                    [f"Today, it's {list(choice.values())[0]}", list(choice.keys())[0]]
                    )
        else:
            message_set.append(f"Today, it's... {choice}")

        for message in message_set:
            await ctx.send(message)

        return

    @commands.command(name="hug")
    async def hug_cmd(self, ctx):
        content = ctx.message.content.split()
        if len(content) > 1:
            recipient = content[1]
        else:
            recipient = ctx.author.display_name
        hug_str = f"VirtualHug VirtualHug VirtualHug hugs to {recipient} for being a lovely person!! VirtualHug VirtualHug VirtualHug"
        await ctx.send(hug_str)

    @commands.command(name="archive_quote")
    async def archive_quote_cmd(self, ctx):
        with open("archived_quotes.txt", "a") as bio_archive:
            bio_archive.write(f'{ctx.author.name}: "{ctx.message.content}"\n')
        return None

    #@commands.check(self.is_mod)
    @commands.command(name="_source")
    async def _source(self, srcname):
        await self._src(srcname.message.content.split()[1])
        # TODO: Everything
        return None

    @commands.command(name="foxdoc")
    async def send_foxdot_docs(self, ctx):
        await ctx.send("https://foxdot.org/docs/")
        return

    # show a link on stream
    @commands.command(name="link")
    async def display_random_media(self, ctx):
        link = ctx.message.content.split()[1]
        whitelist = ['youtube','twitter', 'tiktok', 'twitch']
        if any([url in link for url in whitelist]):
            try:
                response = urllib.request.urlopen(link)
            except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
                await ctx.send("Not a valid url; try again hackers")
                return
        # TODO:
        # gard1ok: You can check for redirects by requesting to the url first (seperately, with urllib or something)
        #
        status_code = response.getcode()
        if status_code != 200:
            await ctx.send("Not a valid url; try again hackers")
            return
        # Add to request queue
        if ctx.message.author.is_mod or ctx.message.author.display_name == 'girlwithbox' or ctx.message.author.is_subscriber:
            await self.set_browser_src("random_link", link)
            await self.toggle_src("random_link")
        else:
            self.requests['count'] += 1
            request_id = self.requests['count']
            self.requests[str(request_id)] = link
            await ctx.send(f"Request #{request_id} added to queue!")
        return

    @commands.check(is_mod)
    @commands.command(name="approve")
    async def approve_request(self, ctx):
        request_id = ctx.message.content.split()[1]
        try:
            requested_url = self.requests.pop(request_id)
        except KeyError:
            await ctx.send(f"Request #{request_id} not found :(")
            return

        await self.set_browser_src("random_link", requested_url)
        await self.set_visible("random_link") # set to visible
        return None

    # Channel point redemption
    async def add_to_box_cmd(self, username, msg):
        print("Returned")
        return f"You want to have a message? {msg}"

    @commands.command(name='daunte')
    async def daunte(self, ctx):
        await ctx.send(f"TW: Police Violence -- https://www.theguardian.com/us-news/2021/apr/12/minnesota-police-shooting-daunte-wright")
        await ctx.send(f"If you can, consider donating to support Daunte's girlfriend and their son: https://www.instagram.com/p/CNkyQbJHoWM/")
        return


    @commands.command(name='stocks') # Check the stock mrkt
    async def stocks(self, ctx):
        # TODO: Return real-time fluctuations in the mrkt
        return

    @commands.command(name='buy') #BUY the stock mrkt
    async def buy(self, ctx):
        # TODO: Buy stocks, save usr stocks
        return

    @commands.command(name='sell') # Sell the stock mrkt
    async def sell(self, ctx):

        return

if __name__ == "__main__":
    bot = Bot()
    bot.run()
