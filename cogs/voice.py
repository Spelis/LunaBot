from http import client
import json
import discord
from discord.ext import commands
import asyncio
import func
import database_conf
from logs import Log

class Queue:
    """Represents The Queue"""

    q: list[func.YTDLSource | func.SpotifySource] = []
    loop = False

    def __init__(self):
        pass  # is there anything to do?


class GuildData:
    """Represents a guild in Voice cache

    Attributes:
        guild_id (int): Guild ID
        generator_id (int): Voice channel generator ID
        channels (list): List of temporary voice channel IDs
    """

    guild_id: int
    generator_id: int
    channels: list[int]
    queue: Queue = Queue()  # * dont save this in the db

    def __init__(
        self,
        guild: discord.Guild,
        generator_id: int | None = None,
        channels: list[int] | None = None,
    ):
        self.guild_id = guild.id if isinstance(guild, discord.Guild) else guild
        self.generator_id = generator_id
        self.channels = channels or []

    def to_json(self):
        return json.dumps(
            {
                "guild_id": self.guild_id,
                "generator_id": self.generator_id,
                "channels": self.channels,
            }
        )


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Voice chat shenanigans including music and sfx"
        self.emoji = "🎵"
        self.voice_data: dict[int, GuildData] = {}

    async def on_load(self):
        async for guild in self.bot.fetch_guilds():
            await self.load_voice_data_from_persistent(guild.id)
            Log['voice'].info(
                f"Config for guild {guild.id}: has been loaded successfully: {self.voice_data[guild.id]}"
            )

    @commands.hybrid_group("voice", description="Voice command group")
    async def voice(self, ctx):
        """Voice command group"""
        if ctx.invoked_subcommand is None:
            command_list = ", ".join(
                [f"{c.name}" for c in self.voice.commands]
                if len(self.voice.commands) > 0
                else ["none"]
            )
            await ctx.send(
                embed=func.Embed()
                .title("You must choose a sub command!")
                .description("Available sub-commands: " + command_list)
                .embed,
                ephemeral=True,
            )

    async def load_voice_data_from_persistent(self, guild_id: int):
        voice_generator_channel_id = (
            await database_conf.get_server_config(guild_id)
        ).get("voice_creation_channel_id")
        if voice_generator_channel_id is None:
            Log['voice'].warning(
                f"Voice generator channel not found for guild {guild_id}. Caching as None."
            )
        self.voice_data[guild_id] = GuildData(
            guild_id, generator_id=voice_generator_channel_id
        )

    def get_or_create_default_cache_entry(self, guild: discord.Guild):
        if guild.id not in self.voice_data:
            self.voice_data[guild.id] = GuildData(guild)
        return self.voice_data[guild.id]

    async def set_voice_generator_channel(self, guild_id: int, channel_id: int):
        await database_conf.set_server_voice_creation_channel(guild_id, channel_id)
        self.voice_data[guild_id].generator_id = channel_id

    @voice.command("info")
    async def vcinfo(self, ctx):
        """Get various info about the voice channels"""
        await ctx.send(
            embed=func.Embed()
            .title("TempChannel Info")
            .description(
                f"{'\n'.join([x.to_json() for x in self.voice_data.values()])}"
            )
            .embed
        )

    @voice.command("temphub")
    async def temphub(self, ctx, channel: discord.VoiceChannel):
        """Creates the Voice Channel generator."""
        await ctx.defer(ephemeral=True)
        await self.set_voice_generator_channel(ctx.guild.id, channel.id)
        await ctx.send(
            f"Voice channel generator has been set to {channel.name}", ephemeral=True
        )
        
    @voice.command("temprename")
    async def temprename(self,ctx,name:str=None):
        """Rename your temporary voice channel (remake required)"""
        if name is None:
            name = f"{ctx.author.display_name}'s Voice"
            
        await database_conf.set_channel_name(ctx.author.id,name)
        
        await ctx.send(f"Renaming {ctx.author.display_name}'s Voice to \"{name}\"")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild
        config = self.get_or_create_default_cache_entry(guild)
        channame = str((await database_conf.get_server_config(guild.id)).get("ChanName", f"{member.display_name}'s Channel"))
        if after.channel and after.channel.id == config.generator_id:
            channel = await member.guild.create_voice_channel(
                name=channame, category=after.channel.category
            )
            await member.move_to(channel)
            config.channels.append(channel.id)
        if before.channel and before.channel.id in config.channels:
            if after.channel and after.channel.id == before.channel.id:
                # User did not leave, so we don't give a fuck
                return
            if len(before.channel.members) == 0:
                config.channels.remove(before.channel.id)
                await before.channel.delete()

    async def _join(self, ctx):
        try:
            if ctx.author.voice is None:
                await ctx.send("You are not in a voice channel.", ephemeral=True)
                return
            channel = ctx.author.voice.channel
            await channel.connect()
        except:
            pass
        return channel

    async def _leave(self, ctx):
        try:
            if ctx.voice_client is None:
                await ctx.send("I am not in a voice channel.", ephemeral=True)
                return
            await ctx.voice_client.disconnect()
        except:
            pass

    async def _play(self, ctx):
        await self._join(ctx)
        player = self.voice_data[ctx.guild.id].queue.q[0]
        client = ctx.voice_client
        client.play(
            player, after=lambda e: self.bot.loop.create_task(self.q_after_song(ctx))
        )
        return player

    async def q_after_song(self, ctx):
        if not self.voice_data[ctx.guild.id].queue.loop:
            self.voice_data[ctx.guild.id].queue.q.pop(
                0
            )  # remove last played song from the queue if user doesnt want to loop
        if not len(self.voice_data[ctx.guild.id].queue.q) > 0:
            await ctx.send(embed=func.Embed().title("Queue Finished!").embed)
            return
        player = self.voice_data[ctx.guild.id].queue.q[0]
        await ctx.send(
            embed=func.Embed()
            .title("Playing next song...")
            .description(f"Playing: {player.title} by {player.uploader}")
            .embed
        )

    @voice.command("join")
    async def join(self, ctx):
        """Join a voice channel"""
        channel = await self._join(ctx)
        await ctx.send(f"Joined {channel.name}", ephemeral=True)

    @voice.command("leave")
    async def leave(self, ctx):
        """Leave the current voice channel"""
        await self._leave(ctx)
        await ctx.send("Left the voice channel", ephemeral=True)

    @voice.command("play")
    async def vplay(self, ctx):
        """Play the queue"""
        player = await self._play(ctx)
        await ctx.send(
            embed=func.Embed()
            .title("Started Playing!...")
            .description(f"Playing: {player.title} by {player.uploader}")
            .embed
        )
        

    @voice.command("pause")
    async def vpause(self, ctx):
        """Pause the current youtube video"""
        ctx.voice_client.pause()
        await ctx.send("Paused the queue", ephemeral=True)

    @voice.command("stop")
    async def vstop(self, ctx):
        """Stop playing"""
        client = ctx.voice_client
        client.stop()
        self.voice_data[ctx.guild.id].queue.q.clear()
        await ctx.send(embed=func.Embed().title("Stopped 🛑").embed)
        
    @voice.command("loop")
    async def vloop(self, ctx, loop: bool = None):
        """Loop the current youtube video"""
        if loop is None:
            loop = not self.voice_data[ctx.guild.id].queue.loop
        self.voice_data[ctx.guild.id].queue.loop = loop
        await ctx.send(
            embed=func.Embed()
            .title("🔄 Loop " + ("enabled" if loop else "disabled"))
            .embed
        )
        
    @voice.command("queue")
    async def vqueue(self, ctx):
        """Show the queue"""
        queue = self.voice_data[ctx.guild.id].queue.q
        if len(queue) == 0:
            await ctx.send(
                embed=func.Embed()
                .title("Queue")
                .description("\n".join(list(map(lambda x: f"🎵 {x.title} by {x.uploader}",self.voice_data[ctx.guild.id].queue.q))))
                .embed
            )
        
    @voice.command("skip")
    async def vskip(self, ctx):
        """Skip the current youtube video"""
        await self.q_after_song(ctx)

    @voice.group("youtube")
    async def yt(self, ctx):
        """Youtube command group"""
        if ctx.invoked_subcommand is None:
            command_list = ", ".join(
                [f"{c.name}" for c in self.yt.commands]
                if len(self.yt.commands) > 0
                else ["none"]
            )
            await ctx.send(
                embed=func.Embed()
                .title("You must choose a sub command!")
                .description("Available sub-commands: " + command_list)
                .embed,
                ephemeral=True,
            )

    @yt.command("song")
    async def ytqsong(self, ctx, url):
        """Play a youtube video"""
        await self._join(ctx)
        player = await func.YTDLSource.from_url(url)
        self.voice_data[ctx.guild.id].queue.q.append(player)
        await self._play(ctx)
        await ctx.send(
            embed=func.Embed()
            .title("Added to queue!")
            .description(f"🎵 {player.title} by {player.uploader}")
            .embed
        )
        
    @yt.command("list")
    async def ytqlist(self, ctx, url):
        """Play a youtube playlist"""
        await self._join(ctx)
        playlist = await func.YTDLSource.from_playlist(url)
        for song in playlist:
            player = await func.YTDLSource.from_url(song['url'])
            self.voice_data[ctx.guild.id].queue.q.append(player)
        await ctx.send(
            embed=func.Embed()
            .title("Added to queue!")
            .description("\n".join(list(map(lambda x: f"🎵 {x.title} by {x.uploader}", playlist))))
            .embed
        )
        await self._play(ctx)

    @voice.group("spotify")
    async def sp(self, ctx):
        """Spotify command group"""
        if ctx.invoked_subcommand is None:
            command_list = ", ".join(
                [f"{c.name}" for c in self.sp.commands]
                if len(self.sp.commands) > 0
                else ["none"]
            )
            await ctx.send(
                embed=func.Embed()
                .title("You must choose a sub command!")
                .description("Available sub-commands: " + command_list)
                .embed,
                ephemeral=True,
            )

    @sp.command("song")
    async def spsong(self, ctx, url):
        """Add a spotify song to the queue"""
        await self._join(ctx)
        player = await func.SpotifySource.from_url(url)
        self.voice_data[ctx.guild.id].queue.q.append(player)
        await self._play(ctx)


async def setup(bot):
    v = Voice(bot)
    await bot.add_cog(v)
    await v.on_load()
