import asyncio
import logging
import random
from async_timeout import timeout
from helpers.song_queue import SongQueue

# Huge props goes to vbe0201 https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
# For help and inspiration

class Music():

    def __init__(self, bot, ctx, voice, logger):
        self.bot = bot
        self.ctx = ctx

        #self.is_playing = False
        self.logger = logger
        self.current = None
        self.voice = voice
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.voice_states = {}
        self._loop = False
        self._volume = 0.5
        #self.volume = self._volume
        self.skip_votes = set()

        self.players = {}
        self.queues = {}

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def get_current(self):
        return self.current

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def add_song(self, song):
        await self.songs.put(song)

    def skip(self):
        self._stop()

    def _stop(self):
        self.voice.stop()
        
    async def _stop_loop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

    def pause(self):
        self.voice.pause()

    def resume(self):
        if not self.is_playing:
            self.play_next_song()   
        else:
            self.voice.resume() 

    def play_next_song(self, error=None):
        self.next.set()        

    def shuffle(self):
        self._stop()
        random.shuffle(self.songs._queue)
        self.play_next_song() 

    async def audio_player_task(self):
        while True:
            try:
                self.next.clear()
                if not self._loop:
                    try:
                        async with timeout(180):
                            self.current = await self.songs.get()
                    except asyncio.TimeoutError as e:
                        self.logger.error(f"bot timed out: {e}")
                        self.bot.loop.create_task(self._stop_loop())
                        return
                    except Exception as e:
                        self.logger.error(f"bot timed out: {e}")
                        self.bot.loop.create_task(self._stop_loop())
                        print(e)
                        return
                curr = self.current[1]
                curr.source.volume = self._volume
                self.voice.play(curr.source, after=self.play_next_song)
                await self.add_reactions()
                await self.next.wait()
            except Exception as e:
                self.logger.error(f"Song_Queue, player error: {e}")
                print(e)
                pass

    async def add_reactions(self):
        msg = await self.current[1].source.channel.send(embed=self.current[1].build_embed())
        await msg.add_reaction('▶️')
        await msg.add_reaction('⏯')
        await msg.add_reaction('⏩')
        await msg.add_reaction('⏹')
        #await msg.add_reaction('🔂')
        await msg.add_reaction('🔀')
        await msg.add_reaction('❤️')

    def toggle_next(self):
        self.ctx.loop.call_soon_threadsafe(self.next.set)

    def check_queue(self, id):
        if self.queues[id] != []:
            player = self.queues[id].pop(0)
            self.players[id] = player
            player.start()


