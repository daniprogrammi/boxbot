# Load user info from db via chatters.py or something
# Create new users and add user info to db via commands from chatters py
import aiosqlite
import attr
from twitchio.ext import commands
from datetime import datetime
from utils.chatters import UserDB
import asyncio
import sqlite3

from pymongo import MongoClient 

client = MongoClient("mongodb://localhost:27017")
db = client.get_database("streamDB")
collection = db.get_collection("userInfo")
users = collection.find({}, {'_id':0, 'username': 1})
userlist = []
for doc in users:
    userlist.append(doc["username"])


# db = UserDB()
# loop = asyncio.get_running_loop()
# userlist_task = loop.create_task(db.getAllUsers())
#userlist = await asyncio.wait(db.getAllUsers())# userlist_task.result()

class UsersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = UserDB()

    async def populate_commands(self):
        self.userlist = await self.db.getAllUsers()

    @commands.command(name="new")
    async def make_new_user_entry(self, ctx):
        name = ctx.message.author
        try:
            await self.db.add_user_to_db(name)
        except:
            await ctx.send("User already in db!")
        return

    @commands.command(aliases=userlist)
    async def dyncommand(self, ctx: commands.Context, attribute=None, value=None):
        username = ctx.message.content.split()[0].strip('!') # ctx.command.name won't work here bc we're using an alias
        print(username)
        if value and (username.lower() != ctx.message.author.display_name.lower()):
            await ctx.send("You can't change another person's info")
        else:
            if attribute and not value:
                # Get this attr
                try:
                    result = await self.db.getUserAttr(username, attribute)
                except:
                    await ctx.send("User attribute not set I guess idk")
                    return

                await ctx.send(f"{username}.{attribute} = {result}")
                return
            
            if attribute and value:
                try:
                    await self.db.addtouser(username, attribute, value)
                except:
                    await ctx.send("Oooops....")
                    return
                
                await ctx.send("Set that thing!")
                return

            if not attribute and not value:
                try:
                    result = await self.db.getUser(username)
                except Exception as e:
                    print(e)
                    await ctx.send("User not in database :/")
                    return

                if not result:
                    await ctx.send(f"User: {username} not in db")
                    return

                msg = f"For user {username}, pronouns: {result.get('pronouns', None)}, location: {result.get('location', None)}, club penguin: {result.get('club_penguin', None)}"
                await ctx.send(msg)

        return


def prepare(bot: commands.Bot):
    bot.add_cog(UsersCog(bot))

def breakdown(bot: commands.Bot):
    bot.remove_cog(UsersCog)

