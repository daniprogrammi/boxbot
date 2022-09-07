import os, sys, re
from twitchio.ext import commands
import urllib3
import random
from time import sleep
 
class GenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.project_str = None
        self.obs = bot.get_cog("ObsCog")
    

    @commands.command(name="todo")
    async def todo(self, ctx:commands.Command):
        #TODO: Make a todo command
        pass

    @commands.command(name="box")
    async def box(self, ctx) -> None:
        basepath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.curdir))))
        basepath = os.path.join(basepath, "OBS_Scene_Switch_Assets")

        choice = random.choice(['audio', 'images', 'videos', 'gifs', 'text'])
        path = os.path.join(basepath, choice)
        value = os.path.join(path, random.choice(os.listdir(path))) if choice != 'text' else None
        if value: 
            value = value.replace('/mnt/c/', 'C:\\')
            value = value.replace('/', '\\')

        if choice == 'audio':
            print("Loading... " + choice)
            #do something with the source called audio
            await self.obs._setSourceSettings("audio", {"local_file": value})
            await self.obs._toggleSource("audio", True)
            sleep()
            pass
        elif choice == 'images':
            print("Loading... " + choice)
            # do something with the source called 'image'
            await self.obs._setSourceSettings("image", {"file": value})
            await self.obs._toggleSource("image", True)
            pass
        elif choice == 'videos' or choice == 'gifs':
            # use video source
            print("Loading... " + choice)
            await self.obs._setSourceSettings("videos", {"playlist": [{"value": value, 'hidden': False, 'selected': False}]})
            await self.obs._toggleSource("videos", True)
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
            ])

            await ctx.send("What's in the box?")
            await ctx.send(text)

        return

    @commands.command(name="lurk")
    async def lurk(self, ctx: commands.Context):
        await ctx.send(f"{ctx.message.author.display_name} retreated to the safety of the box 👁️ 👁️ (thank you for the lurk!)")
        return
    
    @commands.command(name="so", aliases=["shoutout"])
    async def shoutout(self, ctx: commands.Context, username):
        category = None # self.bot.get_category(user)?????
        url = None # either append username to twitch.tv or do it a smart way
        await ctx.send(f"CorgiDerp Shout out to {username} CorgiDerp If you want to watch some extreme {{game}} gameplay, follow {username} at {{url}} I hear they're amazing!)")
        return


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
    
    @commands.command(name="hrc")
    async def hrc(self, ctx):
        await ctx.send("Join and share the Human Rights Campaign for Trans & Non-binary peoples' rights https://www.hrc.org/campaigns/count-me-in")

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

    @commands.command(name="abortions")
    async def abortions(self, ctx):
        await ctx.send("Donate to the national abortion fund here: https://abortionfunds.org/")
        await ctx.send("List of abortion funds by state: https://docs.google.com/document/d/1T-aDTsZXnKhMcrDmtcD35aWs00gw5piocDhaFy5LKDY/")
        await ctx.send("If you are in need of resources check out https://www.reddit.com/r/auntienetwork and https://www.reddit.com/r/abortion <3")
        return

    @commands.command(name="project")
    async def project(self, ctx):
        if self.project_str:
            await ctx.send(self.project_str)
        else:
            await ctx.send("project not set! set with chproject")
        return

    #@commands.check(is_mod)
    @commands.command(name="chproject")
    async def chproject(self, ctx):
        self.project_str = " ".join(ctx.message.content.split()[1:]).capitalize()
        await ctx.send("Changed project!")
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

def prepare(bot: commands.Bot): 
    bot.add_cog(GenCog(bot))

def breakdown(bot: commands.Bot):
    bot.remove_cog("GenCog")   