# Std lib
import socket
import os, sys, re
import requests
import json
import urllib
import asyncio
import random
import time
from dotenv import dotenv_values

# OBS
import simpleobsws

# Twitch Libs
import twitchio
from twitchio.ext import commands

# My libs
import admin

ENCODING = "utf-8"

class Bot(commands.Bot):
    # Bot's internal methods
    def __init__(self):
        self.config = dotenv_values() # load .env file
        super().__init__(
                token=self.config["TWITCH_OAUTH_TOKEN"],
                client_id="adbcgdfja",
                nick=self.config['BOT_NAME'],
                prefix="!", 
                initial_channels=[self.config["CHANNEL"]],
                )

        
        self.bot_uptime = time.time()
        self.requests = {'count': 0}

        self.fight_client = None
        # just names
        self.player1 = None
        self.player2 = None

        self.link_buffer = os.path.join(os.curdir, "buffers", "links.txt")
        self.envvars = {'AUTOLOAD_MODULES': ['admin'], 'BOT_ADMIN': 'girlwithbox', 'DEBUG': 'critical'} 

    
if __name__ == "__main__":
    bot = Bot()
    bot.load_module("admin")
    bot.run()