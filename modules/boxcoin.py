import os, sys, re
from twitchio.ext import commands
from twitchio.ext import routines

import urllib3
import random

from time import sleep
from utils.chatters import UserDB
from datetime import datetime

class BoxCoin(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        # db 
        self.db = UserDB()
        self.rate = .20 # Get rate from finance api thing

    async def _init(self, user):
        # SECRET FORMULA HERE
        user = await self.db.getUser(user)
        # If multiplier is set then this user can buy and sell in the chat
        if not user.get('multiplier', None):
            mult = await self._checkUserClout(user)
            await self.db.addtouser('multiplier', mult)
        else:
            print("User added")

        # TODO: Determine limits per user... (market regulations)
        return

    async def _buy(self, user, amount):
        userObject = await self.db.getUser(user)
       
        if not userObject or not userObject.get('multiplier'):
            # Add user to db
            await self.db.add_user_to_db(user)
            await self._init(user)
        
        current_stonks = userObject.get('stonks')
        
        if current_stonks < amount * self.rate:
            # User cannot buy this
            return False
        else:
            new_stonks = current_stonks - (amount*self.rate)
        await self.db.addtouser('stonks', new_stonks)
        return new_stonks

    async def _sell(self, user, amount):
        userObject = await self.db.getUser(user)
       
        if not userObject or not userObject.get('multiplier'):
            # Add user to db
            await self.db.add_user_to_db(user)
            await self._init(user)

        current_stonks = userObject.get('stonks')
        if current_stonks < (amount * self.rate):
            # Not enough stonks to sell
            return False
        else:
            new_stonks = current_stonks + (amount * self.rate)
        await self.db.addtouser('stonks', new_stonks)
        return new_stonks
        

    async def _checkDBForUser(self, user):
        userObj = await self.db.getUser(user)
        return userObj

    async def _checkUserClout(self, user):
        # Get badges... etc
        userObj = await self._checkDBForUser(user)
        #todo: check if followed first
        if not userObj or not userObj.get('followed_date'):
            gwb = (await self.bot.fetch_users(names=['girlwithbox']))[0].id
            userId = (await self.bot.fetch_users(names=[f'{user}']))[0].id
            data = await self.bot._http.get_user_follows(to_id=gwb, from_id=userId)
            data = data[0] if data else None
            
            if data:
                print(data)
                followed_date = data['followed_at']
                print(followed_date)

                await self.db.addtouser(user, 'followed_date', value=followed_date)

        else:
           followed_date = userObj.get('followed_date')
        
        followed_date = datetime.strptime(followed_date, '%Y-%m-%dT%H:%M:%SZ')
        multiplier = .05 * followed_date.timestamp()

        return multiplier

    async def _updateMultiplier(self, user):
        #SECRET FORMULA FOR UPDATING HERE
        return
    
    @routines.routine(minutes=42)
    async def routine_something_another(self):
        await self.bot.get_channel('girlwithbox').send("$$$$$$$ummer of $bxc #grindset")
        return

    @routines.routine(minutes=10)
    async def polluserClout(self):
        for user in self.db.getAllUsers():
            userObj = await self.db.getUser(user)
            if not userObj.get('multiplier'):
                await self._init(user)
            await self._updateMultiplier(user)
            
        return
    #####

    @commands.command(name="buy")
    async def buy(self, ctx: commands.Context, amount=None):
        buyer = ctx.message.author.display_name
        if not amount:
            amount = 1
        res = await self._buy(buyer, amount)
        if res:
            await ctx.send(f"$ucce$$fully bought {amount} of $bxn $$$$! Hashtag grindset hashtag risendgrind")
        else:
            await ctx.send(f"Uh-oh $orry brokey you don't have enough CLOUT to buy {amount} $bxc")
        return

    @commands.command(name="sell")
    async def sell(self, ctx: commands.Context, amount=None):
        seller = ctx.message.author.display_name

        if not amount:
            amount = 1
        res = await self._sell(seller, amount)
        if res:
            await ctx.send(f"SELLING? IN THIS ECONOMY???? {amount} $bxc sold!")
        else:
            await ctx.send(f"Uh-oh you didn't have enough to sell #getonyourgrindset #make$omecoin$$$")
        return

    @commands.command(name="startstuff")
    async def startstuff(self, ctx):
        await ctx.send("Starting the stuff")
        self.routine_something_another.start()
        return
        
    @commands.command(name="stopstuff")
    async def startstuff(self, ctx):
        await ctx.send("Stopping! the stuff")
        self.routine_something_another.stop()
        return

def prepare(bot: commands.Bot): 
    bot.add_cog(BoxCoin(bot))

def breakdown(bot: commands.Bot): # Unload module
    bot.remove_cog("BoxCoin")   

# if __name__ == "__main__":
#     main()

## TODO: 
# 1. Tie $$$bxc to some functions like !vlc_link
# 2. Make a ticker so that we can see how our coin is doing compared to some others
# 4. PROFIT $$$
# 3. Alias vlc_link to link
# 5. Install vim extension 