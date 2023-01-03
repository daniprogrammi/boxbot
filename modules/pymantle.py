import asyncio
from pyppeteer import launch
from twitchio.ext import commands


class Pymantle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def init_page(self):
        browser = await launch()
        page = await browser.newPage()
        await page.goto('https://semantle.pimanrul.es/')
        self.page = page
        return

    async def _guess(self, word):
        element = await self.page.querySelector('#guess')
        print(element)
        set_guess = await self.page.evaluate('(element, word) => element.setAttribute(\'textContent\', word)', element, word)
        print(set_guess)
        curr_word = await self.page.evaluate('(element) => element.textContent', element)
        print(curr_word)
        await self.page.querySelector("input[type=submit]").click()
        return

    @commands.command(name='guess')
    async def guess(self, ctx: commands.Command, word):
        await self._guess(word)
        return

    @commands.command(name='pymantle')
    async def init(self, ctx: commands.Command):
        await self.init_page()
        return
        
    # Guess input:#guess, submit: .guess-submit; hints: .hint-button
    # Output: ----> guess-entry, guess-index, guess-word, guess-similarity, guess-flavor, guess-rank
def prepare(bot: commands.Bot): 
    bot.add_cog(Pymantle(bot))

def breakdown(bot: commands.Bot): # Unload module
    bot.remove_cog("Pymantle")   
