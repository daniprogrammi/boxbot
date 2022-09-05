import os, sys, re
from typing import Literal

from twitchio import AuthenticationError
from twitchio.ext import commands
import urllib3


class GenCog(commands.Cog):
    """ General commands cog """
    def __init__(self, bot):
        self.bot = bot
        self.project_str = None
        self.obs = bot.get_cog("ObsCog")

    @commands.command(name="link")
    async def link(self, ctx: commands.Context, requested_url):
        """ Link to a project """
        link = ctx.message.content.split()[1]
        whitelist = ['youtube', 'twitter', 'tiktok', 'twitch']
        if any([url in link for url in whitelist]):
            try:
                http = urllib3.PoolManager()
                response = http.request('GET', link)
            except AuthenticationError as e:
                await ctx.send("Not a valid url; try again hackers")
                return
            await ctx.send("Can't do that")
            return

        status_code = response.status
        if status_code != 200:
            await ctx.send("Not a valid url; try again hackers")
            return

        link_src: Literal["link"] = "link"
        await self.obs._setSourceSettings(link_src, {"url": requested_url})
        await self.obs._toggleSource(link_src, True)

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
        await ctx.send("I appreciate everyone who subs, but it's definitely better spent on donations.")
        await ctx.send(self.aapi)  # I think this may work?
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

    @commands.command(name="project")
    async def project(self, ctx):
        """Displays the current project"""
        if self.project_str:
            await ctx.send(self.project_str)
        await ctx.send("project not set! set with chproject")
        return

    # @commands.check(is_mod)
    @commands.command(name="chproject")
    async def chproject(self, ctx):
        """Change the project string"""
        self.project_str = " ".join(ctx.message.content.split()[1:]).capitalize()
        await ctx.send("Changed project!")
        return

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
