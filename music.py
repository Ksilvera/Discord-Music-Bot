import discord
from discord.ext import commands
from ast import alias
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        #music
        self.is_playing = False
        self.is_paused = False

        #Array containing song,channel
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}

        self.vc = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

    def search_youtube(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=False)["title"]
            return{'source':item, 'title':title}
        search = VideosSearch(item, limit=1)
        return{'source':search.result()["result"][0]["link"], 'title':search.result()["result"][0]["title"]}
    
    async def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            url = self.music_queue[0][0]['source']

            self.music_queue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
            song = data['url']
            self.vc.play(discord.FFmpegPCMAudio(song, executable="ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.is_playing = False
    
    async def play_music(self,ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            url = self.music_queue[0][0]['source']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
            song = data['url']
            self.vc.play(discord.FFmpegPCMAudio(song, executable="ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        
        else:
            self.is_playing = False
    
    @commands.command(name="play", aliases=["p","playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send("You need to connect to a voice channel first")
            return
        if self.is_paused:
            self.vc.resume()
        else:
            song = self.search_youtube(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect Format try another keyword. This could be because of playlist or livesteam format.")
            else:
                if self.is_playing:
                    await ctx.send(f"**#{len(self.music_queue)+2} - '{song['title']}'** added to the queue")
                else:
                    await ctx.send(f"**'{song['title']}'** added to the queue")
                self.music_queue.appened([song, voice_channel])
                if self.is_playing == False:
                    await self.play_music(ctx)
    
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
    
    @commands.command(name="resume", aliases=["r"], help="Resumes playing with the discord bot")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
    
    @commands.command(name="skip", aliases=["s"], help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #play next song in queue if there is one
            await self.play_music(ctx)
    
    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self,ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += f"#{i+1} -" + self.music_queue[i][0]['title'] + "\n"
        
        if retval != "":
            await ctx.send(f"queue:\n{retval}")
        else:
            await ctx.send("No music in the queue")

    @commands.command(name="clear", aliases=["c","bin"], help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")
    
    @commands.command(name="stop", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def disconnect(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
    
    @commands.command(name="remove", help="Removes last song added to the queue")
    async def remove(self, ctx):
        self.music_queue.pop()
        await ctx.send("Last song removed")