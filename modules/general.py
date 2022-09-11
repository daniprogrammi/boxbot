import os, sys, re
import json
from typing import Literal, Any

import twitchio
from twitchio import AuthenticationError
from twitchio.ext import commands, routines
import urllib3
import random
from time import sleep

todo_list = []


class GenCog(commands.Cog):
    """ General commands cog """

    def __init__(self, bot):
        self.bot = bot
        self.project_str = None
        self.obs = bot.get_cog("ObsCog")

    @staticmethod
    def get_cache(self):
        """

        :return:
        :rtype:
        """
        path = os.path.dirname(os.path.abspath(os.curdir))  # parent dir twitch_chatbot
        base_path = os.path.join(path, "buffers")

        cache_path = os.path.join(base_path, "stream-cache.json")
        if os.path.exists(cache_path):
            cache = json.load(open(cache_path, 'w'))
            return cache_path, cache
        return cache_path, None

    @commands.command(name="todo")
    async def todo(self, ctx: commands.Command):
        """

        :param ctx:
        :type ctx:
        """
        # TODO: Make a todo command
        pass

    @commands.command(name="box")
    async def box(self, ctx: commands.Context) -> None:
        """
            # TODO: Refactor this code
        """
        basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.curdir))))
        basepath = os.path.join(basepath, "OBS_Scene_Switch_Assets")

        choice = random.choice(['audio', 'images', 'videos', 'gifs', 'text'])
        path = os.path.join(basepath, choice)
        value = os.path.join(path, random.choice(os.listdir(path))) if choice != 'text' else None
        if value:
            value = value.replace('/mnt/c/', 'C:\\')
            value = value.replace('/', '\\')
        if not value:
            await ctx.send("Uh-oh the box didn't find anything this time; try again plskthnx")

        if choice == 'audio':
            print("Loading... " + choice)
            try:
                await self.obs.set_source_settings("audio", {"local_file": value})
                await self.obs.toggle_source("audio", True)
                sleep(5)  # Why is this necessary?? -- I don't remember ... 
            except twitchio.TwitchIOException as e:
                print
                await ctx.send("Uh-oh the box didn't find anything this time; try again plskthnx")
            pass
        elif choice == 'images':
            print("Loading... " + choice)
            # do something with the source called 'image'
            if 'chonky_gosling' in value:
                await ctx.send("It's chonky gosling! YayGarf")
            elif 'gwbcoin' in value:
                await ctx.send("oh...")
            elif 'tiddie' in value:
                await ctx.send("Happy Halloween! https://twitter.com/frenziedlanes/status/1566491081629642752")

            await self.obs.set_source_settings("image", {"file": value})
            await self.obs.toggle_source("image", True)

            pass
        elif choice == 'videos' or choice == 'gifs':
            # use video source
            print("Loading... " + choice)
            await self.obs.set_source_settings("videos",
                                               {"playlist": [{"value": value, 'hidden': False, 'selected': False}]})
            await self.obs.toggle_source("videos", True)
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

    @commands.command(name="lurk")
    async def lurk(self, ctx: commands.Context) -> None:
        """ Lurk command """
        await ctx.send(
            f"{ctx.message.author.display_name} retreated to the safety of the box 👁️ 👁️ (thank you for the lurk!)")

    @commands.command(name="wolfstep")
    async def welcome(self, ctx: commands.Context) -> None:
        """ Welcome the user to the stream """
        await ctx.send("""
        Wolf is the greatest stepper of all time!
        """)

    @routines.routine(seconds=600, iterations=5)
    async def social_media(self): # Start of social media routine!
        """ Post a social media link every 10 minutes """
        await self.bot.send("Follow all of my socials!")

    @commands.command(name="so", aliases=["shoutout"])
    async def shoutout(self, ctx: commands.Context, category: Any | None) -> None:
        """ Shoutout command """
        username: str = ctx.message.author.display_name
        user_channel_info = await self.bot.fetch_channel(username)
        if user_channel_info:
            category = user_channel_info.game_name  # self.bot.get_category(user)?????

        url = f"www.twitch.tv/{username}"  # Or do this a smart way eventually
        if user_channel_info:
            await ctx.send(
                f"CorgiDerp Shout out to {username} CorgiDerp If you want to watch some extreme {category} gameplay, follow {username} at {url} I hear they're amazing!")
        await ctx.send(
            f"CorgiDerp Shout out to {username} CorgiDerp!! Follow them at {url} I hear they're amazing!")

    @commands.command(name="welcome")
    async def welcome(self, ctx: commands.Context) -> None:
        """ Welcome the user to the stream """
        await ctx.send("""
        Welcome in raiders peepoHey. I'm the girl! This channel has been super programming focused recently
        but sometimes I play games here too! The vibe is chaotic casual, drinks are in the back and we hope
        you enjoy your stay peepoHey
        """)

    @commands.command(name="sub")
    async def sub(self, ctx: commands.Context):
        """ Sub command """
        await ctx.send(
            "I appreciate everyone who subs, but it's definitely better spent on donations to charity! Check out some of the ones in the commands")
        await ctx.send("Here are some links to resources, info and places to donate"
                       " to help stop anti-Asian violence https://anti-asianviolenceresources.carrd.co/")  # Return Text from the command instead.
        return

    @commands.command(name="hrc")
    async def hrc(self, ctx: commands.Context):
        """ This is a command to display the HRC link """
        await ctx.send(
            "Join and share the Human Rights Campaign for Trans & Non-binary peoples' rights https://www.hrc.org/campaigns/count-me-in")

    @commands.command(name="aapi")
    async def aapi(self, ctx: commands.Context):
        """ Returns the aapi information """
        await ctx.send("""
        Here are some links to resources, info and places to donate
        to help stop anti-Asian violence https://anti-asianviolenceresources.carrd.co/
        """)

    @commands.command(name="blm")
    async def blm(self, ctx: commands.Context):
        """ Returns the Black Lives Matter information """
        await ctx.send("""Here are some links to resources, info and donation links to support
        Black Lives Matter https://blacklivesmatters.carrd.co/""")

    @commands.command(name="tiktok")
    async def tiktok(self, ctx: commands.Context):
        """ Return the tiktok link """
        await ctx.send("Follow me on TikTok! https://www.tiktok.com/@girlwithbox")
        return

    @commands.command(name="abortions")
    async def abortions(self, ctx: commands.Context):
        """This is a command that is only available to mods"""
        await ctx.send("Donate to the national abortion fund here: https://abortionfunds.org/")
        await ctx.send(
            "List of abortion funds by state: https://docs.google.com/document/d/1T-aDTsZXnKhMcrDmtcD35aWs00gw5piocDhaFy5LKDY/")
        await ctx.send(
            "If you are in need of resources check out https://www.reddit.com/r/auntienetwork and https://www.reddit.com/r/abortion <3")
        return

    @commands.command(name="project")
    async def project(self, ctx: commands.Context):
        """Displays the current project"""
        # Check project_str then cache
        path = os.path.dirname(os.path.abspath(os.curdir))  # parent dir twitch_chatbot
        base__path = os.path.join(path, "buffers")

        cache = os.path.join(base__path, "stream-cache.json")
        if self.project_str:
            await ctx.send(self.project_str)
        elif os.path.exists(cache):
            with json.load(open(cache, 'r')) as stream_cache:
                current_project = stream_cache.get('project', None)
                if current_project:
                    self.project_str = current_project
        await ctx.send("project not set! set with chproject")
        return

    # @commands.check(is_mod)
    @commands.command(name="chproject")
    async def chproject(self, ctx: commands.Context):
        """Change the project string"""
        self.project_str = " ".join(ctx.message.content.split()[1:]).capitalize()
        await ctx.send("Changed project!")

        cache_path, cache = self.get_cache()
        if cache:
            cache['project'] = self.project_str
        else:
            cache = {'project': self.project_str}

        json.dump(cache, open(cache_path, 'w+'))  # Store for later
        return

    @commands.command(name="discord")
    async def discord(self, ctx: commands.Context):
        """ Sends the discord link """
        await ctx.send("Join my discord! [Put pressure on me to maintain it] https://discord.gg/4RXASvcG6k")

    @commands.command(name="twitter")
    async def twitter(self, ctx: commands.Context):
        """ Sends the twitter link """
        await ctx.send("DxCat For more box-related shenanigans follow me on twitter www.twitter.com/girlwithbox DxCat")

    @commands.command(name="github")
    async def github(self, ctx: commands.Context):
        """ Sends the GitHub link """
        await ctx.send("Find my code on GitHub! https://github.com/Danicodes")


def prepare(bot: commands.Bot):
    """ Prepares the cog for use """
    bot.add_cog(GenCog(bot))


def breakdown(bot: commands.Bot):
    """ Breaks down the cog """
    bot.remove_cog("GenCog")
