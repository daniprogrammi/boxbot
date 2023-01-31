import re
import aiosqlite
from numpy import insert
from twitchio.ext import commands
import urllib3
import yt_dlp
from datetime import datetime
import random

import sqlalchemy
import sqlite3

DATABASE = "requests.db"

class VlcCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.obs = self.bot.get_cog("ObsCog")
        self.playing_now = None
        self.bot.loop.create_task(self.db_init())

    async def get_media(self, link, link_src="vlc_link"):
        # Allow for media from twitter, twitch clips, insta? potentially
        # WILL NOT ALLOW FOR LINKS WITHOUT MEDIA
        with yt_dlp.YoutubeDL({}) as ytl:
            try:
                info = ytl.extract_info(link, download=False)
            except yt_dlp.utils.ExtractorError as e:
                # Return none here
                return

            formats = info.get('formats')[::-1]
            # acodec='none' means there is no audio
            try:
                best_video = next(f for f in formats
                            if (f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none') 
                            or (f.get('format_id', None) in ['1080', '720'])) # Twitch clips don't contain codec info
            except RuntimeError as e:
                # Stop Iteration
                return
            
            title = info.get('fulltitle') if info.get('fulltitle', None) else info.get('title')
            uploader = info.get('uploader')
            play_url = best_video['url']
            
            self.playing_now = f"{title} uploaded by {uploader}" #TODO: tie to an event sub of the media player
            await self.obs._setSourceSettings(f"{link_src}", {"playlist": [{"value": play_url, 'hidden': False, 'selected': False}]})
            await self.obs._toggleSource(f"{link_src}", True)

        return

    @commands.command(name="vlc_link", aliases=['link', 'url'])
    async def display_media_vlc(self, ctx: commands.Context, link):
        # TODO QUERY DB TO SEE IF URL ALREADY ADDED
        
        queue_pos = "SELECT MAX(queue_position) as 'max' FROM requests;"
        async with self.conn.execute(queue_pos) as queue_pos_cur:
            queue_pos = await queue_pos_cur.fetchone()
            queue_pos = queue_pos["max"] if queue_pos else None

        with yt_dlp.YoutubeDL({}) as ytl:
            try:
                info = ytl.extract_info(link, download=False)
            except yt_dlp.utils.ExtractorError as e:
                # Return none here
                return
            
            formats = info.get('formats')[::-1]
            # acodec='none' means there is no audio
            try:
                best_video = next(f for f in formats
                            if (f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none') 
                            or (f.get('format_id', None) in ['1080', '720'])) # Twitch clips don't contain codec info
            except StopIteration as e:
                 # Stop Iteration
                 await ctx.send("Couldn't find a playable format for this link :(")
                 return
            
            new_pos = queue_pos + 1 if queue_pos else 1

            await self.insert_request(id, link, ctx.message.author.display_name, info.get('fulltitle'), info.get('uploader'),
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

    @commands.command(name="nightride")
    async def nightride(self, ctx:commands.Context):
        nightride_link = "https://www.youtube.com/watch?v=cZRj9Sk0IPc"
        await self.get_media(nightride_link, "nightride")
        return
    
    async def nightridePlay(self):
        await self.obs._toggleSource("nightride", True)
        await self.obs.setMedia("nightride", "play")
        return

    async def nightridePause(self):
        await self.obs._toggleSource("nightride", False)
        await self.obs.setMedia("nightride", "stop")
        return

    @commands.command(name="pause_radio")
    async def nightride_pause(self, ctx:commands.Context):
        await self.nightridePause()
        return

    @commands.command(name="play_radio")
    async def nightride_play(self, ctx:commands.Context):
        await self.nightridePlay()
        return

    # Define some callbacks for nightride    


    @commands.command(name="kbb", aliases=['kate_bush_break'])
    async def kbb(self, ctx:commands.Context):
        katebush = { "Running_Up_That_Hill" : "https://www.youtube.com/watch?v=wp43OdtAAkM",
                    "Wuthering_Heights": "https://www.youtube.com/watch?v=-1pMMIe4hb4",
                    "The_Sensual_World": "https://www.youtube.com/watch?v=h1DDndY0FLI",
                    "Cloudbusting": "https://www.youtube.com/watch?v=pllRW9wETzw",
                    }

        choice = random.choice(list(katebush.values()))
        await self.get_media(choice) 
        return

    @commands.command(name="21st", aliases=['21', 'september'])
    async def twentyfirst(self, ctx:commands.Context):
        song = "https://www.youtube.com/watch?v=Gs069dndIYk"
        await self.get_media(song) 
        return

    @commands.command(name="approve")
    async def approve_request(self, ctx: commands.Context, queue_pos=None):
        if not ctx.author.is_mod or not ctx.author.is_vip:
            await ctx.send("Sorry you can't do that")
            return 

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

    async def auto_approve(self, request_id, requestor):
        # Auto approve links from a requestor if they're long term community member, vip, mod
        update_cmd = """
                    UPDATE requests SET approved = 'T' where id=(?); 
                    """  
        
        async with self.conn.execute(update_cmd, request_id) as approve:
            await self.conn.commit()

    @commands.command(name="play")
    async def play_next(self, ctx: commands.Context, queue_pos=None):
        res = await self.obs._getMediaInputStatus("nightride")
        
        if res["mediaState"] == "OBS_MEDIA_STATE_PLAYING":
            await self.nightridePause()

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
        uploader = row["creator"]

        self.playing_now = f"{title} uploaded by {uploader}" #TODO: tie to an event sub of the media player
        self.last_requestor = row["requestor"]

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
            try:
                info = ytl.extract_info(link, download=False)
            except yt_dlp.utils.ExtractorError as e:
                # Return none here
                return


            formats = info.get('formats')[::-1]
            # acodec='none' means there is no audio
            try:
                best_video = next(f for f in formats
                            if (f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none') 
                            or (f.get('format_id', None) in ['1080', '720'])) # Twitch clips don't contain codec info
            except RuntimeError as e:
                 # Stop Iteration
                 return
            
            url = best_video.get('url')
            return url
        

    @commands.command(name="playing")
    async def whatsplaying(self, ctx:commands.Context):
        if self.playing_now is None:
            await ctx.send("Nothing is playing...") 
        else:
            await ctx.send(f"Playing Now: {self.playing_now}")
        
        return

    async def _getQueue(self, columns=['queue_position', 'title', 'approved']):
        # DANGER 
        retrieve_queue = f"""
                            SELECT {','.join("?"*len(columns))} FROM requests WHERE queue_position is NOT NULL;
                        """
        async with self.conn.execute(retrieve_queue, columns) as cur:
            results = await cur.fetchall()

        return results 

    @commands.command(name="queue")
    async def getQueue(self, ctx:commands.Context):
        results = await self._getQueue()

        await ctx.send("Currently in queue:")
        for result in results:
            queue_pos, title, approved = result
            await ctx.send(f"{title} at position {queue_pos}, {approved}")
        return

    ############### EVENT CALLBACKS
    async def media_event_callback(self, eventData):
        print(eventData)

    async def media_playback_started(self, eventData):
        # Pause other media if playing (spotipy/youtube somehow)
        pass

    async def media_playback_ended(self, eventData):
        if (eventData['inputName'] in ['vlc_link', 'link']):
            self.playing_now = None
            await self.obs._toggleSource('vlc_link', False) # Turn off video source
            await self.obs._toggleSource('link', False) # Turn off video source
        elif (eventData['inputName'] == 'audio'):
            await self.obs._toggleSource('audio', False)
        
        # Resume radio play
        await self.nightridePlay()
        return

    #TODO: Make this not a twitch command and call this function on init to register all callbacks 
    @commands.command(name="register_callbacks")
    async def register_callbacks(self, ctx:commands.Context):
        self.obs.obs_ws.register_event_callback(self.media_event_callback, "MediaInputActionTriggered")
        self.obs.obs_ws.register_event_callback(self.media_playback_started, "MediaInputPlaybackStarted")
        self.obs.obs_ws.register_event_callback(self.media_playback_ended, "MediaInputPlaybackEnded")
        await ctx.send("Callbacks registered")
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
    