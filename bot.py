import socket
import os, sys, re
from twitchio.ext import commands
from ansimarkup import ansiprint as print
import urllib
import asyncio
import simpleobsws
import random
import glob
import json
from controller_to_obs import TwitchController 

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



#COMMAND_LIST = {
#        "box": box_cmd,
#        "donate": donate_cmd,
#        "hug": hug_cmd,
#        "addtobox": add_to_box_cmd,
#        "addtoarchive": archive_quote_cmd,
#        "toggleDB": toggle_DyBrowse_cmd,
#        "refresh_cam": cam_refresh_cmd,
#        "display": display_random_media,
#        }
#
#MOD_ONLY_CMDS = {
#        "addtobox": add_to_box_cmd,
#        "addtoarchive": archive_quote_cmd,
#        "toggleDB": toggle_DyBrowse_cmd,
#        }
#
#ME_ONLY_CMDS = {"refresh_cam": cam_refresh_cmd, "display": display_random_media}


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
        
        self.requests = {'count': 0}


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
        await self.handle_commands(message)

    # TODO: Event Listeners
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
        result = await self.make_request(request)
        return result

    async def move_scene_item(self, sourceName, new_x, new_y):
        request = "SetSceneItemProperties"
        data = {"item": sourceName, "position": {"x":new_x, "y":new_y}}
        result = await self.make_request(request, data)
        return        

    async def twitch_controller(self):
        controller = TwitchController()
        sourceName = "HDCAM_Plain"
        current_scene_items = await self.get_current_scene_items()
        print("Sources?", current_scene_items['sources'])
        print("Items")

        vals_generator = controller.joystick_source()
        async for vals in vals_generator:
            # TODO: Add/Subtract from original position
            # Numpy, batch requests
            
            await self.move_scene_item(sourceName, vals[0], vals[1])

        #TODO: stuff with the switch to cycle through sources
        return

    async def set_browser_src(self, sourceName, newurl):
        request = "SetSourceSettings"
        data = {"sourceName": sourceName, "sourceSettings": {"url": newurl}}
        result = await self.make_request(request, data)
        return
 

    ############################################################################
    #                         Twitch Commands                                  #
    ############################################################################
   
    
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
        ctx.send(f"x:{result['position']['x']}, y:{result['position']['y']}")
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
    def _is_command_username(function):
        @wraps(function)

    @commands.command(name="set")
    async def user_cmd(self, ctx):
        # TODO: check if user is in db, load existing user_obj if so,
        # else create user obj and set attr
        content = ctx.message.content.split()

        user = ctx.message.author # User Obj
        username = ctx.message.author.display_name
        attr = content[1] 
        attr_arg = content[2]

        #!set name Dani
        #> ok
        #!girlwithbox.name
        #> "Dani"
        return 

    @commands.command(name="project")
    async def project(self, ctx):
        await ctx.send("I'm working on an Arduino controller for OBS! Breaking things and whatnot")
        return

    @commands.command(name="discord")
    async def discord(self, ctx):
        await ctx.send("Join my discord! [Put pressure on me to maintain it] https://discord.gg/4RXASvcG6k")
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
    @commands.command(name="toggle_source")
    async def toggle_source(self, srcname):
        await self.toggle_src(srcname.message.content.split()[1])
        # TODO: Everything
        return None

    @commands.command(name="twitter")
    async def twitter_cmd(self, username, link=None):
        """
        If no tweet provided, then send the url to my twitter page
        otherwise display sent tweet
        """
        if not link:
            twitter_str = """DxCat For more box-related shenanigans follow me on twitter www.twitter.com/girlwithbox DxCat"""
            return twitter_str
        elif link and "twitter" in link and "/status/" in link:
            set_browser_src(link)
            return None
        else:
            return None
    @commands.command(name="foxdoc")
    async def send_foxdot_docs(self, ctx):
        await ctx.send("https://foxdot.org/docs/")
        return

    # Show a link on stream
    @commands.command(name="link")
    async def display_random_media(self, ctx):
        link = ctx.message.content.split()[1]
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
