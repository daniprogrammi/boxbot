import re
import aiosqlite
from twitchio.ext import commands, routines

from pymongo import MongoClient
from datetime import datetime
import random

# The economy of twitch

class UsersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        client = MongoClient("mongodb://localhost:27017")
        self.db = client.get_database("streamDB")
        self.collection = self.db.userInfo

        self.rated = []
        self._requested_title = None


    def getVlcCog(self):
        self.vlc = self.bot.get_cog("VlcCog")

    def getRequestsConnection(self):
        self.requests_conn = self.vlc.conn if self.vlc and self.vlc.conn else None
        self._requested_title = self.vlc.playing_now
        return

    # TEST COG UNLOAD
    # def cog_unload(self):
    #   print("bye :(")
    
    @routines.routine(seconds=600)
    async def message_point_bonus(self):
        if not hasattr(self, 'interval_messages'):
            self.interval_messages = {}
            return

        for chatter_id, val in self.interval_messages.items():
            points = 5 * val
            res = self.collection.update_one({'user_id': chatter_id}, 
                {'$inc': {'points': points}})
        
        self.interval_messages = {} # Clear after updating db this interval

        return

    ## Count messages sent on interval to accrue points
    @commands.command(name="start_points")
    async def start_routines(self, ctx):
        # TODO: Start this automatically
        self.channel = ctx.channel # Bad 
        await self.update_all_points.start()
        await self.message_point_bonus.start()
        return

    @commands.command(name="stop_points")
    async def stop_routines(self, ctx):
        await self.update_all_points.stop()
        await self.message_point_bonus.stop()
        return

    @routines.routine(seconds=300) # 30 for testing
    async def update_all_points(self):
        print("Updating points")
        update_errors = 0
        chatters = self.channel.chatters
        for chatter in chatters:
            try:
                user = await chatter.user()
                user_id = user.id
                await self.update_points(user_id)
            except (TypeError, AttributeError):
                update_errors += 1                
        return

    #@routines.routine(seconds=240)
    async def update_points(self, user_id):
        # Add economy points for a user -- virtual packing peanuts
        await self.set_point_multiplier(user_id)
        userObj = self.collection.find_one({'user_id': user_id})
        if not userObj:
            self.collection.insert_one({'user_id': user_id, 'points': 0})
        else:
            multiplier = userObj.get('multiplier', 1)
            points = userObj.get('points', 1)
            updated_user = self.collection.update_one({'user_id': user_id}, {'$set': {'points': (multiplier * 5) + points }})

        return

    async def set_point_multiplier(self, user_id):
        userObj = self.collection.find_one({'user_id': user_id})
        linkRating = userObj.get('avgLinkRating', 1)/3
        
        twitchUser = (await self.bot.fetch_users(names=[user_id]))[0]
        chatterObj = self.channel.get_chatter(twitchUser.name)

        mod = chatterObj.is_mod
        vip = chatterObj.is_vip
        sub = chatterObj.is_subscriber

        mod = 5 if mod else 1
        vip = 3 if vip else 1
        sub = 2 if sub else 1

        multiplier = max(linkRating, mod, vip, sub)                    
        
        self.collection.update_one({
            'user_id': user_id
            }, {
            "$set": {
                "multiplier": multiplier
                 }
            })
        return

    def getUser():
        # Return partial chatter

        return

    @commands.command(name="points")
    async def points(self, ctx: commands.Context, other_user=None):
        if not other_user:
            userObj = await ctx.author.user()
            user_id = userObj.id
            username = userObj.name
        else:
            twitchUser = (await self.bot.fetch_users(names=[other_user]))[0]
            user_id = twitchUser.id
            username = other_user

        userObj = self.collection.find_one({"user_id": user_id}, {"points": 1})
        
        if not userObj.get("points"):
            await ctx.send(f"Couldn't retrieve virtual packing peanuts for {username}, maybe step your game up?")
            return
        else:
            await ctx.send(f"{username} has accrued {userObj.get('points')} virtual packing peanuts! CoolCat")
            return

    @commands.command(name="give")
    async def give_points(self, ctx: commands.Context, other_user, points=5):
        if not other_user:
            await ctx.send("You need to specify who you're giving the packing peanuts to ya biscuit!")
            return
        
        # Check this user's points
        giver = await ctx.author.user()
        userlist = (await self.bot.fetch_users(names=[other_user]))
        if len(userlist) == 0:
            await ctx.send(f"Couldn't find this {other_user} you speak of... honestly, a lil sus")
            return

        receiver = userlist[0]
        giverObj = self.collection.find_one({"user_id": giver.id}, {"points": 1})
        
        if not giverObj.get("points"):
            await ctx.send(f"You don't have any packing peanuts to give away, you fraud! >:( ")
            return
        elif giverObj.get("points") < points:
            await ctx.send(f"You don't have enough packing peanuts to give away!!")
            return
        else:
            receiverObj = self.collection.find_one({"user_id": receiver.id}, {"points": 1})
            
            giverBalance = giverObj.get("points") - points
            receiverBalance = receiverObj.get("points", 0) + points 

            self.collection.update_one({"user_id": giver.id}, {"$set": {"points": giverBalance}})
            self.collection.update_one({"user_id": receiver.id}, {"$set": {"points": receiverBalance}})

            await ctx.send(f"{giver.name} gave {other_user} {points} virtual packing peanuts! How sweet :D")
            return

    @commands.command(name="take")
    async def take_points(self, ctx:commands.Context, other_user):
        taker = await ctx.author.user()
        userlist = (await self.bot.fetch_users(names=[other_user]))
        
        if len(userlist) == 0:
            await ctx.send(f"Couldn't find this {other_user} you speak of... honestly, a lil sus")
            return
        
        takee = userlist[0]
        takeeObj = self.collection.find_one({"user_id": takee.id}, {"points": 1})

        if not takeeObj.get("points"):
            await ctx.send(f"You picked a bad mark {taker.name}, {other_user} has 0 packing peanuts to steal")
            return

        choice = (random.choices(["hit", "miss"], weights=(60, 40), k=1))[0]
        if choice == "miss":
            await ctx.send(f"{taker.name}'s conscience just kicked in, they don't want to scam {other_user} anymore")

        takeeBalance = takeeObj.get("points") 
        loot = random.randint(1, takeeBalance)
    
        takeeBalance = takeeBalance - loot

        # https://stackoverflow.com/questions/39358092/range-as-dictionary-key-in-python
        if loot >= 1 and loot < 51: 
            message = f"{taker.name} threatens {other_user} with a water gun!... {other_user} felt sorry for them and gave them {loot} packing peanuts!",
        elif loot >= 51 and loot < 201:
            message = f"{loot} packing peanuts just fell out of {other_user}'s pocket! And into {taker.name}'s pocket :O",
        elif loot >= 201 and loot < 601:
            message = f"{taker.name} just got {other_user} to buy into their ponzi scheme! Nice that's +{loot} packing peanuts for {taker.name}",
        elif loot >= 601 and loot < 2001:
            message = f"{taker.name} convinced {other_user} to buy their followerbots! {other_user} spent {loot} packing peanuts!",
        elif loot >= 2001 and loot < 100001:
            message = f"Holy shit, {taker.name} just got {other_user} to invest in their \'hot dogs for cats\' business to the tune of {loot} packing peanuts!!!"
        elif loot >= 100001:
            message = f"{taker.name} just SOLD {other_user} on the darkweb for {loot} packing peanuts!!"

        self.collection.update_one({"user_id": taker.id}, {"$inc": {"points": loot}})
        self.collection.update_one({"user_id": takee.id}, {"$set": {"points": takeeBalance}})

        await ctx.send(message)
        return        
        

    @commands.command(name="messages")
    async def messageCount(self, ctx: commands.Context):
        # Count messages for chatter
        userObj = await ctx.author.user()
        username = userObj.name
        user_id = userObj.id
           

        found_user = self.collection.find_one({"user_id": user_id}, {'message_count': 1})
        message_count = found_user.get("message_count")
        if not message_count:
            await ctx.send(f"Couldn't retrieve messages for {username}, yell at the streamer!")
        else:
            await ctx.send(f"{username} has sent {message_count} messages here since the economy began")
        return  
    
    @commands.Cog.event()
    async def event_message(self, message):
        if "WHISPER" in message.raw_data or message.echo:
            # Skip whispers
            return

        # Count messages
        userObj = await message.author.user()
        
        username = userObj.name 
        user_id = userObj.id
       
        found_user = self.collection.find_one({"user_id": user_id})
        if not found_user:
            found_user = self.collection.insert_one(
                {
                "user_id": user_id,
                "username": username,
                "message_count": 1
                })
        else:
            updated_user = self.collection.update_one({"user_id": user_id}, 
            {"$inc": {"message_count": 1}})

        # Update the message interval counter 
        if hasattr(self, 'interval_messages'): 
            if self.interval_messages.get(f'{user_id}'):
                self.interval_messages[f'{user_id}'] += 1
            else:
                self.interval_messages[f'{user_id}'] = 1
 
        return


    
    async def getChatter(self, channel_name, username):
        userObjs = await self.bot.fetch_users(names=[channel_name, username])
        meObj = userObjs[0]

    async def fetchfollow(self, channel_name, username):
        userObjs = await self.bot.fetch_users(names=[channel_name, username])
        meObj = userObjs[0] 
        userObj = userObjs[1]
        res = await userObj.fetch_follow(meObj)
        return res.followed_at
        
    @commands.command(name="followage")
    async def followage(self, ctx:commands.Command, username):
        if not username:
            await ctx.send("Need a user to query the status of")
        
        timedelta = await self.fetchfollow(ctx.channel.name, username)
        await ctx.send(f"{username} has been following since {timedelta}")

    @commands.command(name="test_obama")
    async def test_db_stuff(self, ctx:commands.Context):
        obamaObj = self.collection.find_one({"username": "obama"})
        print(obamaObj)
        await ctx.send(f"{obamaObj.get('profile_picture')}") 
        return 

    async def getLinkRating(self, user):
        # Get the average link rating for this user
        userObj = await self.collection.find_one({"username"}, {"avgLinkRating": 1, "_id": 0})
        if not userObj:
            self.collection.insert_one({"username": user})
            return None
        else:
            return userObj

    async def updateLinkRating(self, user, score):
        userObj = self.collection.find_one({"username": user}, {"linkRating": 1, 'avgLinkRating': 1})
        if not userObj:
            self.collection.insert_one({"username": user})
            userObj = self.collection.find_one({"username": user})

        linkRating = userObj.get('linkRating', None)
        if score > 10:
            score = 10
        elif score < 0:
            score = 0

        if not linkRating:
            linkRating = {'count': 1, 'score': score}
        else:
            linkRating['count'] += 1
            linkRating['score'] += score
        
        avgLinkRating = linkRating['score']/linkRating['count']
        
        updateObj = {
            "avgLinkRating": avgLinkRating,
            "linkRating": linkRating
        }

        userObj = self.collection.update_one({"username": user}, {"$set": updateObj})
        return

    @commands.command(name="last_requestor")
    async def getLastRequestor(self, ctx: commands.Context):
        self.getRequestsConnection()
        if not self.vlc.last_requestor:
            await ctx.send(f"Could not get last requestor :(")
        else:
            await ctx.send(f"Link last requested by: {self.vlc.last_requestor}")
        
        return

    @commands.command(name="rate")
    async def rate_link(self, ctx: commands.Context, score):
        self.getVlcCog()

        rater = ctx.author.display_name
        if rater in self.rated:
            await ctx.send(f"{rater} already rated this video >:( ")
            return

        if self.vlc and self._requested_title != self.vlc.playing_now:
            # Playing a new video
            self.rated = []

        self.getRequestsConnection()
        if not self.vlc.last_requestor:
            await ctx.send(f"No requestor set? Maybe cry about it??")
            return

        try:
            score = float(score)
        except ValueError as e:
            await ctx.send(f"Invalid rating \'{score}\', must be a number from 0 to 10")
            return
        
        if self.vlc and self.vlc.last_requestor:
            await self.updateLinkRating(self.vlc.last_requestor, score)
            self.rated.append(rater) # When the rating is successful add them to list of raters
        
        await ctx.send(f"{ctx.author.display_name} rated {self.vlc.last_requestor} {score}/10")
        return

    async def check_queue(self):
        # Check for links currently waiting to be played
        results = await self.vlc._getQueue(columns=['requestor', 'queue_position'])
        return results



def prepare(bot: commands.Bot): 
    bot.add_cog(UsersCog(bot))

def breakdown(bot: commands.Bot): # Unload module
    bot.remove_cog("UsersCog")   
 