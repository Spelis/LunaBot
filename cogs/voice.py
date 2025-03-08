import json
import discord
from discord.ext import commands

import func
import server_config


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
        await self.bot.wait_until_ready()
        async for guild in self.bot.fetch_guilds():
            await self.load_voice_data_from_persistent(guild.id)
            print(
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
            await server_config.get_server_config(guild_id)
        ).get("voice_creation_channel_id")
        if voice_generator_channel_id is None:
            print(
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
        await server_config.set_server_voice_creation_channel(guild_id, channel_id)
        self.voice_data[guild_id].generator_id = channel_id

    @voice.command("info")
    async def vcinfo(self, ctx):
        """Get various info about the voice channels"""
        await ctx.send(
            embed=func.Embed()
            .title("Voice Bot Info")
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

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild
        config = self.get_or_create_default_cache_entry(guild)
        if after.channel and after.channel.id == config.generator_id:
            channel = await member.guild.create_voice_channel(
                name=f"{member.name}'s Voice", category=after.channel.category
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

    @yt.command("play")
    async def ytplay(self, ctx, url):
        """Play a youtube video"""
        await self._join(ctx)
        client = ctx.voice_client
        player = await func.YTDLSource.from_url(url)
        client.play(player, after=lambda e: self.bot.loop.create_task(self.ytstop(ctx)))
        await ctx.send(
            embed=func.Embed()
            .title("Playing 🎵")
            .description(f"Playing **{player.title}**")
            .footer(url)
            .embed
        )

    @yt.command("stop")
    async def ytstop(self, ctx):
        """Stop playing"""
        client = ctx.voice_client
        client.stop()
        await ctx.send(embed=func.Embed().title("Stopped 🛑").embed)


async def setup(bot):
    v = Voice(bot)
    await bot.add_cog(v)
    await v.on_load()
