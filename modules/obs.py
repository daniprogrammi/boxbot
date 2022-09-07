import os, sys, re
from requests import request
from twitchio.ext import commands
from twitchio import Message
import asyncio
import simpleobsws


class ObsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False)
        self.obs_ws = simpleobsws.WebSocketClient(
            url=f"ws://{self.bot.config['HOSTNAME']}:{self.bot.config['PORT']}",
            password=self.bot.config["PASSWORD"],
            identification_parameters=parameters
        )
        print(f"initializing obs with loop: {self.obs_ws.loop}")
        self.bot.loop.create_task(self.obs_ws.connect())
        # self.bot.loop.create_task(self.obs_ws.wait_until_identified()) #I GUESS??
        print("Obs cog :o")

    # TODO: READ
    # async def event_ready(self):
    #     print(f"Obs Ready")
    #     await self.initialize_obsws()

    @commands.command(name='obsinit')
    async def initialize_obsws(self):
        parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks=False)
        self.obs_ws = simpleobsws.WebSocketClient(
            url=f"ws://{self.bot.config['HOSTNAME']}:{self.bot.config['PORT']}",
            password=self.bot.config["PASSWORD"],
            identification_parameters=parameters
        )
        print(f"initializing obs with loop: {self.obs_ws.loop}")
        self.loop = self.obs_ws.loop  # Yeaaah...?
        await self.obs_ws.connect()
        await self.obs_ws.wait_until_identified()  # I GUESS??
        return

    def cog_unload(self):
        print("Breaking down cog, disconnecting...")  # Not called on remove_cog/unload
        if self.obs_ws:
            self.obs_ws_disconnect_task = self.bot.loop.create_task(self.obs_ws.disconnect())
        return

    @commands.command(name='obsversion')
    async def getversion(self, ctx):
        request = simpleobsws.Request('GetVersion')
        ret = await self.obs_ws.call(request)
        if ret.ok():
            obs_version = ret.responseData['obsVersion']
            await ctx.send(f"Version: {obs_version}")

    # # ############################################
    # #               Helpers
    ################################################
    async def make_request(self, request, data=None, verbose=False):
        request = simpleobsws.Request(request, data)
        if not self.obs_ws:
            print("Obs websocket not initialized, cannot make request")
            return  # sys.exit(0)
        result = await self.obs_ws.call(request)
        # Make a request with the given data
        if not result.ok():
            print(f"Error [{result.requestType}]: {result.requestStatus.comment}")
            return None

        if verbose:
            print("Request returned: ", result)
        return result.responseData

    async def _setSceneItemEnabled(self, sceneItemName, enabled, sceneName=None):
        requestName = "SetSceneItemEnabled"
        if not sceneName:
            sceneName = await self._getCurrentScene()
        sceneItemId = await self._getSceneItemId(sceneItemName, sceneName=sceneName)
        data = {"sceneName": sceneName, "sceneItemId": int(sceneItemId), "sceneItemEnabled": enabled}
        await self.make_request(requestName, data)
        return

    async def _getCurrentScene(self):
        requestName = "GetCurrentProgramScene"
        result = await self.make_request(requestName)
        return result["currentProgramSceneName"] if result else None

    async def _getSceneItemId(self, sourceName, sceneName=None):
        requestName = "GetSceneItemId"
        data = {"sourceName": sourceName}
        if sceneName:
            data["sceneName"] = sceneName
        else:
            sceneName = await self._getCurrentScene()
            data["sceneName"] = sceneName

        if not sceneName:
            return None

        result = await self.make_request(requestName, data)
        if result:
            return result["sceneItemId"]
        else:
            return None

    async def _isItemEnabled(self, sceneItemName, sceneName=None):
        sceneItemId = await self._getSceneItemId(sceneItemName)
        if not sceneName:
            sceneName = await self._getCurrentScene()

        data = {"sceneItemId": int(sceneItemId), "sceneName": sceneName}
        requestName = "GetSceneItemEnabled"

        result = await self.make_request(requestName, data)
        return result["sceneItemEnabled"] if result else None

    async def _toggleInputMute(self, inputName):
        requestName = "ToggleInputMute"
        data = {"inputName": inputName}
        res = await self.make_request(requestName, data)
        return res

    async def _getMediaInputStatus(self, inputName):
        requestName = "GetMediaInputStatus"
        data = {"inputName": inputName}
        res = await self.make_request(requestName, data)
        return res

    async def _setSourceSettings(self, inputName, inputSettings, overlay=True):
        requestName = "SetInputSettings"
        data = {"inputName": inputName, "inputSettings": inputSettings}
        await self.make_request(requestName, data)
        return

    async def _getSceneItems(self):
        requestName = "GetSceneItemList"
        sceneName = await self._getCurrentScene()
        data = {"sceneName": sceneName}
        res = await self.make_request(requestName, data)
        return res["sceneItems"] if res else None

    async def _toggleSource(self, sourceName, state=None):
        if not state:
            enabled = await self._isItemEnabled(sourceName)
            newState = not enabled
        else:
            newState = state

        await self._setSceneItemEnabled(sourceName, newState)

        return

    # # ############################################
    # #               Commands!!!
    ################################################

    @commands.command(name="getItems")
    async def getSceneItems(self, ctx: commands.Context):
        res = await self._getSceneItems()
        if res:
            print(res)
        return

    @commands.command(name="set_visible")  # !set_visible sceneItemName true/false
    async def setSceneItemState(self, ctx: commands.Context):
        command = ctx.message.content.split()
        if len(command) > 2:
            sceneItemName = command[1]
            setItem = command[2]
        else:
            await ctx.send("Need more arguments!")
            return

        if setItem in ["true", "t"]:
            setItem = True
        else:
            setItem = False

        await self._setSceneItemEnabled(sceneItemName, setItem)
        return

    @commands.command(name='curscene')
    async def getCurrentScene(self, ctx: commands.Context):
        result = await self._getCurrentScene()
        await ctx.send(f"{result}")
        return

    @commands.command(name="enabled")
    async def isItemEnabled(self, ctx: commands.Context):
        command = ctx.message.content.split()
        print(command)
        if len(command) > 1:
            sceneItemName = command[1]
        else:
            await ctx.send("Expected a scene item")
            return

        result = await self._isItemEnabled(sceneItemName)
        await ctx.send(f"{result}")
        return

    @commands.command(name="inputlist")
    async def getInputList(self, ctx: commands.Context):
        requestName = "GetInputList"
        response = await self.make_request(requestName)
        print(response)
        return

    @commands.command(name="getInputSettings")
    async def getInputSettings(self, ctx: commands.Context):
        command = ctx.message.content.split()

        inputName = command[1]
        requestName = "GetInputSettings"

        data = {"inputName": inputName}
        res = await self.make_request(requestName, data)

        print(res)
        return

    @commands.command(name="setInputSettings")
    async def setInputSettings(self, ctx: commands.Context):
        command = ctx.message.content.split()

        inputName = command[1]
        requestName = "SetInputSettings"

        data = {"inputName": inputName}
        res = await self.make_request(requestName, data)

        print(res)
        return

    @commands.command(name="getOutput")
    async def getOutputSettings(self, ctx: commands.Context, outputName):
        requestName = "SetOutputSettings"
        data = {"outputName": outputName}

        res = await self.make_request(requestName, data)
        if res:
            await ctx.send(res)
        else:
            await ctx.send("No")
        return

    @commands.command(name="setOutput")  # outputName, outputSettings
    async def setOutputSettings(self, ctx: commands.Context, outputName, outputSetting, outputSettingValue):
        requestName = "SetOutputSettings"
        data = {f"{outputSetting}": outputSettingValue, "outputName": outputName}
        res = await self.make_request(requestName, data)
        if res:
            await ctx.send(":thumbsup:")
        else:
            await ctx.send("NotLikeThis")
        return

    @commands.command(name="getMediaStatus")
    async def getMediaInputStatus(self, ctx: commands.Context, mediaName):
        res = await self._getMediaInputStatus(mediaName)

        if res:
            await ctx.send(res)
        else:
            await ctx.send("NotLikeThis")
        return

    async def setMedia(self, source, action):
        if action.lower() == "play":
            triggeraction = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
        elif action.lower() == "pause":
            triggeraction = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
        elif action.lower() == "stop":
            triggeraction = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP"
        elif action.lower() == "restart":
            triggeraction = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
        else:
            return

        requestName = "TriggerMediaInputAction"
        data = {"inputName": source, "mediaAction": triggeraction}

        await self.make_request(requestName, data)
        return

    @commands.command(name="media")
    async def mediaAction(self, ctx: commands.Context, source, action):
        await self.setMedia(source, action)
        return

    @commands.command(name="toggle")
    async def toggleSomething(self, ctx: commands.Context, sourceName):
        await self._toggleSource(sourceName)
        return


def prepare(bot: commands.Bot):
    bot.add_cog(ObsCog(bot))


def breakdown(bot: commands.Bot):  # Unload module
    bot.remove_cog("ObsCog")
