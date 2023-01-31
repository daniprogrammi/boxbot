import os, sys, re
import json # Note to look at orjson
from typing import Literal
from twitchio import AuthenticationError
from twitchio.ext import commands
from twitchio.ext import routines
import urllib3
import random
from time import sleep
import sqlite3
import aiosqlite 

class GenCog(commands.Cog):
    """ General commands cog """
    def __init__(self, bot):
        self.bot = bot
        self.project_str = None
        self.obs = None 
        self.vlc = None
        self.conn = None
        self.bot.loop.create_task(self.connect_to_database())
        
    def obs_init(self):
        self.obs = self.bot.get_cog("ObsCog")

    def vlc_init(self):
        self.vlc = self.bot.get_cog("VlcCog")

    def get_cache(self):
        # TODO: fix this, line 23 fails on json.load
        basepath = os.path.abspath(os.curdir) # parent dir twitch_chatbot
        basepath = os.path.join(basepath, "buffers")

        cache_path = os.path.join(basepath, "stream-cache.json")
            
        try:
            cache = json.load(open(cache_path))
            return cache_path, cache
        except json.JSONDecodeError as e:
            # Cache is currently empty or invalid
            if os.path.getsize(cache_path) == 0:
                # Cache is empty
                return cache_path, None
            else:
               raise json.JSONDecodeError(f"Invalid json syntax in cache: {e}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Cache not found: {e}")

    @commands.command(name="todo")
    async def todo(self, ctx:commands.Command):
        #TODO: Make a todo command
        pass

    async def connect_to_database(self):
        conn = await aiosqlite.connect("database/box.db")
        conn.row_factory = sqlite3.Row
        self.conn = conn
        return

    async def get_urls(self) -> list:
        url_request = """
            SELECT url FROM requests WHERE approved = 'T';
            """
        urls_result = await self.conn.execute(url_request)
        urls = await urls_result.fetchall()
        await urls_result.close()
        return urls

    @commands.command(name="gravy")
    async def gravy(self, ctx: commands.Context) -> None:
        """hell

        Args:
            ctx (commands.Context): _description_
        """
        self.obs_init()
        self.vlc_init()
        
        basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.curdir))))
        basepath = os.path.join(basepath, "OBS_Scene_Switch_Assets") # Path where I store all my random things from the internet
        videopath = os.path.join(basepath, "videos")
        
        value = os.path.join(videopath, "gravy.mp4")

        if value:
            value = value.replace('/mnt/c/', 'C:\\')
            value = value.replace('/', '\\')

            # Pull into another function 
            await self.obs._setSourceSettings("videos", {"playlist": [{"value": value, 'hidden': False, 'selected': False}]})
            await self.obs._toggleSource("videos", True)
            # toggle off after duration of clip, get duration of clip... somehow
            await self.obs._getInputSettings("videos")

        await ctx.send("My nightmare")
        return 
     



    @commands.command(name="box")
    async def box(self, ctx, choice=None) -> None:
        """ Display a random piece of saved media

        Args:
            ctx (commands.Context): Twitchio context object
        """

        # TODO: Auto mute nightride here
        #   
        self.obs_init()
        self.vlc_init()

        basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.curdir))))
        basepath = os.path.join(basepath, "OBS_Scene_Switch_Assets") # Path where I store all my random things from the internet

        # Handle for errors with missing obs and vlc 
        choices = ['audio', 'images', 'videos', 'gifs', 'text', 'link']
        if not self.obs:
            choices = ['text']

        if not self.vlc:
            choices.remove('link')

        if not choice or choice not in choices:
            choice = random.choice(choices)
        
        path = os.path.join(basepath, choice)
        value = os.path.join(path, random.choice(os.listdir(path))) if choice not in ['text', 'link'] else None

        if value:
            value = value.replace('/mnt/c/', 'C:\\')
            value = value.replace('/', '\\')
        if not value and choice not in ['text', 'link']:
            await ctx.send("Uh-oh the box didn't find anything this time; try again plskthnx")
            return

        if choice == 'audio':
            print("Loading... " + choice)
            #do something with the source called audio
            await self.obs._setSourceSettings("audio", {"local_file": value})
            
            # Toggle audio source on and then back off after 10 seconds
            await self.obs._toggleSource("audio", True)
            sleep(10)
            await self.obs._toggleSource("audio", False)
            return

        elif choice == 'images':
            print("Loading... " + choice)
            # do something with the source called 'image'
            if 'chonky_gosling' in value:
                await ctx.send("It's chonky gosling! YayGarf")
            elif 'gwbcoin' in value:
                await ctx.send("oh...")
            elif 'tiddie' in value:
                await ctx.send("Happy Halloween! https://twitter.com/frenziedlanes/status/1566491081629642752")

            await self.obs._setSourceSettings("image", {"file": value})
            await self.obs._toggleSource("image", True)
            sleep(30)
            await self.obs._toggleSource("image", False)
            return

        elif choice == 'videos' or choice == 'gifs':
            # use video source
            print("Loading... " + choice)
            await self.obs._setSourceSettings("videos", {"playlist": [{"value": value, 'hidden': False, 'selected': False}]})
            await self.obs._toggleSource("videos", True)
            # toggle off after duration of clip, get duration of clip... somehow
            await self.obs._getInputSettings("videos")

        elif choice == 'text':
            print("Loading... " + choice)
            text = random.choice(["Box", 
                "struggle!",
                " an even smaller box",
                "cookies",
                "Actually, it's empty",
                "a head!",
                "chocolates",
                "Chonky Ryan Gosling",
                ":)",
                "*screams*",
                "darude sandstorm"
            ])

            await ctx.send("What's in the box?")
            await ctx.send(text)

        # Replace addtobox
        elif choice == 'link':
            urls = await self.get_urls()
            print(urls)
            if urls and len(urls) == 0:
                selected_url = "https://www.youtube.com/watch?v=56RsdDNjGI4"
            else:
                selected_url = random.choice(urls)
                selected_url = selected_url["url"]
            await ctx.send(f"A link from the past... {selected_url}")
            await self.vlc.get_media(selected_url)

        return

    @commands.command(name="lurk")
    async def lurk(self, ctx: commands.Context):
        await ctx.send(f"{ctx.message.author.display_name} retreated to the safety of the box 👁️ 👁️ (thank you for the lurk!)")
        return
    
    @commands.command(name="mastodon")
    async def mastodon(self, ctx: commands.Context):
        await ctx.send(f"hachyderm.io/@girlwithbox")
        return

    @commands.command(name="so", aliases=["shoutout"])
    async def shoutout(self, ctx: commands.Context, username):
        user_channel_info = await self.bot.fetch_channel(username)
        if user_channel_info:
            category = user_channel_info.game_name # self.bot.get_category(user)?????
        
        url = f"www.twitch.tv/{username}" # Or do this a smart way eventually
        if user_channel_info:
            await ctx.send(f"CorgiDerp Shout out to {username} CorgiDerp If you want to watch some extreme {category} gameplay, follow {username} at {url} I hear they're amazing!")
        else:
            await ctx.send(f"CorgiDerp Shout out to {username} CorgiDerp!! Follow them at {url} I hear they're amazing!")
        return

    @commands.command(name="retrommo", aliases=["retro"])
    async def retrommo(self, ctx):
        await ctx.send("Check out RetroMMOs MMO at https://retro-mmo.com/")
        return



    @commands.command(name="welcome")
    async def welcome(self, ctx):
        """ Welcome the user to the stream """
        await ctx.send(
            "Welcome in raiders peepoHey. I'm the girl! This channel has been super programming focused recently"
            "but sometimes I play games here too! The vibe is chaotic casual, "
            "drinks are in the back and we hope you enjoy your stay peepoHey")
        return

    @commands.command(name="sub")
    async def sub(self, ctx):
        """ Sub command """
        await ctx.send("I appreciate everyone who subs, but it's definitely better spent on donations to charity! Check out some of the ones in the commands")
        await self.aapi()  #Edit: Now... I think this should work
        return

    @commands.command(name="hrc")
    async def hrc(self, ctx):
        """ This is a command to display the HRC link """
        await ctx.send(
            "Join and share the Human Rights Campaign for Trans & Non-binary peoples' rights https://www.hrc.org/campaigns/count-me-in")

    @commands.command(name="aapi")
    async def aapi(self, ctx):
        """ Returns the aapi information """
        await ctx.send("Here are some links to resources, info and places to donate"
                       " to help stop anti-Asian violence https://anti-asianviolenceresources.carrd.co/")
        return

    @commands.command(name="blm")
    async def blm(self, ctx):
        """ Returns the Black Lives Matter information """
        await ctx.send("Here are some links to resources, info and donation links to support"
                       " Black Lives Matter https://blacklivesmatters.carrd.co/")
        return

    @commands.command(name="tiktok")
    async def tiktok(self, ctx):
        """ Return the tiktok link """
        await ctx.send("Follow me on TikTok! https://www.tiktok.com/@girlwithbox")
        return

    @commands.command(name="abortions")
    async def abortions(self, ctx):
        """This is a command that is only available to mods"""
        await ctx.send("Donate to the national abortion fund here: https://abortionfunds.org/")
        await ctx.send(
            "List of abortion funds by state: https://docs.google.com/document/d/1T-aDTsZXnKhMcrDmtcD35aWs00gw5piocDhaFy5LKDY/")
        await ctx.send(
            "If you are in need of resources check out https://www.reddit.com/r/auntienetwork and https://www.reddit.com/r/abortion <3")
        return


    async def _puerto_rico(self, destination):
        """Places to donate to in the aftermath of Hurricane Fiona

        Args:
            ctx (_type_): _description_
        """
        
        await destination.send("Donate to local organizations in Puerto Rico in the aftermath or Hurricane Fiona")
        await destination.send("I think this Mutual Aid Network is a great place to start: https://www.bsopr.com/")
        await destination.send("Here's a document of other organizations that you can donate to for both PR and DR: https://docs.google.com/document/d/1hGTkGwqAWZmAK-JUC7aWnHaVenTfWlxAMnUyZ3ON6co/")
        return

    @routines.routine(seconds=10, iterations=5)
    async def _pr_routine(self, destination):
        await self._puerto_rico(destination)
        return

    @commands.command(name="start_routine")
    async def start_routines(self, ctx):
        await self._puerto_rico.start(ctx.channel)
        return

    @commands.command(name="stop_routine")
    async def stop_routines(self, ctx):
        await self._puerto_rico.stop()
        return

    @commands.command(name='pr', aliases=['puerto_rico'])
    async def puerto_rico(self, ctx: commands.Context):
        await self._puerto_rico(ctx.channel)
        return

    @commands.command(name="project")
    async def project(self, ctx):
        """Displays the current project"""
        
        cache_path, cache = self.get_cache()
        
        if self.project_str:
            await ctx.send(self.project_str)
        elif (cache):
            current_project = cache.get('project', None)
            self.project_str = current_project 

        if not self.project_str:
            await ctx.send("project not set! set with chproject")
        return

    # @commands.check(is_mod)
    @commands.command(name="chproject")
    async def chproject(self, ctx):
        """Change the project string"""
        
        if ctx.author.is_mod:
            self.project_str = " ".join(ctx.message.content.split()[1:]).capitalize()
            await ctx.send("Changed project!")
            
            cache_path, cache = self.get_cache()
            
            if cache:
                cache['project'] = self.project_str
            else: 
                cache = {'project': self.project_str}
            # TODO: See if this is working
            json.dump(cache, open(cache_path, 'w+')) # Store for later    
            return
        else:
            await ctx.send("No!")


    @commands.command(name="discord")
    async def discord(self, ctx):
        """ Sends the discord link """
        await ctx.send("Join my discord! [Put pressure on me to maintain it] https://discord.gg/4RXASvcG6k")
        return

    @commands.command(name="twitter")
    async def twitter(self, ctx):
        """ Sends the twitter link """
        await ctx.send("DxCat For more box-related shenanigans follow me on twitter www.twitter.com/girlwithbox DxCat")
        return

    @commands.command(name="github")
    async def github(self, ctx):
        """ Sends the github link """
        await ctx.send("Find my code on GitHub! https://github.com/Danicodes")
        return


def prepare(bot: commands.Bot):
    """ Prepares the cog for use """
    bot.add_cog(GenCog(bot))


def breakdown(bot: commands.Bot):
    """ Breaks down the cog """
    bot.remove_cog("GenCog")
