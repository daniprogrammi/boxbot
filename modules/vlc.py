from gettext import find
import re
import aiosqlite
from numpy import insert
from pyrsistent import get_in
from twitchio.ext import commands
import urllib3
import yt_dlp
from datetime import datetime

import sqlalchemy
import sqlite3

DATABASE = "requests.db"

class VlcCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.obs = self.bot.get_cog("ObsCog")
        self.playing_now = None
        self.bot.loop.create_task(self.db_init())
    
    @commands.command(name="vlc_link")
    async def display_media_vlc(self, ctx: commands.Context, link):
        # TODO QUERY DB TO SEE IF URL ALREADY ADDED
        
        queue_pos = "SELECT MAX(queue_position) as 'max' FROM requests;"
        async with self.conn.execute(queue_pos) as queue_pos_cur:
            queue_pos = await queue_pos_cur.fetchone()
            queue_pos = queue_pos["max"] if queue_pos else None

        with yt_dlp.YoutubeDL({}) as ytl:
            info = ytl.extract_info(link, download=False)

            formats = info.get('formats')[::-1]
            # acodec='none' means there is no audio
            best_video = next(f for f in formats
                        if f['vcodec'] != 'none' and f['acodec'] != 'none')
            
            new_pos = queue_pos + 1 if queue_pos else 1
            await self.insert_request(id, link, ctx.message.author.display_name, info.get('fulltitle'), info.get('creator'),
                         info.get('like_count'), info.get('dislike_count'), queue_position=new_pos)

            await ctx.send(f"Added to queue at position {new_pos}")
        
        return

    ####
    #### Statuses = "NEVER PLAYED", "FINISHED PLAYING", 
    async def insert_request(self, id, url, requestor, title, creator, likes, dislikes, status="NOT PLAYING", approved='F', queue_position=None):
        vals = (url, requestor, title, creator, likes,
                    dislikes, status, approved, queue_position, datetime.today().strftime("%Y-%m-%d"), 0)
        insert_req = f"""
                    INSERT INTO requests (url, requestor, title, creator, likes, dislikes, status, approved, queue_position, requested_date, last_played)
                     VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ;
                    """
        async with self.conn.execute(insert_req, vals):
            await self.conn.commit() 
            assert self.conn.total_changes > 0

        return

    @commands.command(name="approve")
    async def approve_request(self, ctx: commands.Context, queue_pos=None):
        if queue_pos:
            approve_req = """UPDATE requests 
                            SET approved = 'T'
                            WHERE queue_position=(?);
                        """
            await self.conn.execute(approve_req, queue_pos)
        else: # approve the next in queue
            approve_req = """ with next_in_q as (
                                SELECT id FROM requests
                                WHERE queue_position = (SELECT min(queue_position) 
                                                        FROM requests WHERE approved='F' AND queue_position is not NULL)
                                )
                            UPDATE requests
                            SET approved = 'T'
                            WHERE id in (SELECT id FROM next_in_q)
                            ; 
                        """
            await self.conn.execute(approve_req)

        await ctx.send(f"Approved ${queue_pos}" if queue_pos else "Approved next in queue!")
        return



    @commands.command(name="play")
    async def play_next(self, ctx: commands.Context, queue_pos=None):
        if queue_pos:
            find_link = """SELECT * FROM requests WHERE queue_position=(?);"""
            url_req = await self.conn.execute(find_link, queue_pos)
        else:
            find_link = "SELECT * FROM requests WHERE queue_position=1;"
            url_req = await self.conn.execute(find_link)
        
        row = await url_req.fetchone()
        url = row["url"]
        playurl = await self.approve_link(url)
        title = row["title"]
        creator = row["creator"]

        self.playing_now = f"{title} by {creator}" #TODO: tie to an event sub of the media player
        await self.obs._setSourceSettings("vlc_link", {"playlist": [{"value": playurl, 'hidden': False, 'selected': False}]})
        await self.obs._toggleSource("vlc_link", True)
        
        # Update queue_pos subtracting 1 from everything in queue
        update_positions = """
            with all_positions as (
                SELECT id FROM requests WHERE queue_position is not null
                )
            UPDATE requests
            SET queue_position = CASE WHEN queue_position <= 1 then NULL
                                 ELSE queue_position - 1 end
            WHERE id in (SELECT id FROM all_positions)
            ;
        """
        async with self.conn.execute(update_positions) as update_cur:
            await self.conn.commit()

        ergonomic = "Looks uncomfortable; supposedly better for you???"

        return
        
    async def approve_link(self, link):
         with yt_dlp.YoutubeDL({}) as ytl:
            info = ytl.extract_info(link, download=False)

            formats = info.get('formats')[::-1]
            # acodec='none' means there is no audio
            best_video = next(f for f in formats
                        if f['vcodec'] != 'none' and f['acodec'] != 'none')

        # find compatible audio extension
        # audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
        # # vcodec='none' means there is no video
        # best_audio = next(f for f in formats if (
        #     f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext))

            url = best_video['url']
            return url
        

    @commands.command(name="playing")
    async def whatsplaying(self, ctx:commands.Context):
        if self.playing_now is None:
            await ctx.send("Nothing is playing...") 
        else:
            await ctx.send(f"Playing Now: {self.playing_now}")
        
        return

    @commands.command(name="queue")
    async def getQueue(self, ctx:commands.Context):
        retrieve_queue = """
                            SELECT queue_position, title, approved FROM requests WHERE queue_position is NOT NULL;
                        """
        async with self.conn.execute(retrieve_queue) as cur:
            results = await cur.fetchall()

        await ctx.send("Currently in queue:")
        for result in results:
            queue_pos, title, approved = result
            await ctx.send(f"{title} at position {queue_pos}, {approved}")
        await ctx.send(self.queue)
        return

    ############### EVENT CALLBACKS
    async def media_event_callback(self, eventData):
        print(eventData)

    async def media_playback_started(self, eventData):
        pass

    async def media_playback_ended(self, eventData):
        if (eventData['inputName'] == 'vlc_link'):
            self.playing_now = None
        pass

    #TODO: Make this not a twitch command and call this function on init to register all callbacks 
    @commands.command(name="register_callbacks")
    async def register_callbacks(self, ctx:commands.Context):
        self.obs.obs_ws.register_event_callback(self.media_event_callback, "MediaInputActionTriggered")
        self.obs.obs_ws.register_event_callback(self.media_playback_started, "MediaInputPlaybackStarted")
        self.obs.obs_ws.register_event_callback(self.media_playback_started, "MediaInputPlaybackEnded")
        return

    
    # #####  DATABASE FX
    # async def connect_to_database(self, ctx):
    #     await self.db_init()
    #     await ctx.send("Db initted")
    #     return

    async def db_init(self):
        create_db = """
            CREATE TABLE IF NOT EXISTS requests
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                requestor TEXT,
                title TEXT,
                creator TEXT,
                likes INTEGER,
                dislikes INTEGER,
                status TEXT,
                approved TEXT, -- T/F
                queue_position INTEGER,
                requested_date INTEGER,
                last_played INTEGER 
            );
        """

        conn = await aiosqlite.connect("database/box.db")
        await conn.execute(create_db)
        conn.row_factory = sqlite3.Row
        self.conn = conn
        return

    def cog_unload(self):
            if self.conn:
                print("Breaking down cog, disconnecting from db") #Not called on remove_cog/unload
                self.bot.loop.create_task(self.conn.close())
            return


def prepare(bot: commands.Bot): 
    bot.add_cog(VlcCog(bot))

def breakdown(bot: commands.Bot): # Unload module
    bot.remove_cog("VlcCog")   
    