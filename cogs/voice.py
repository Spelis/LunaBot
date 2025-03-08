from discord.ext import commands
import discord
import func
import server_config

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Voice chat shenanigans including music and sfx"
        self.emoji = "🎵"
        self.voicedata = {}
        
    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        for i in self.bot.guilds:
            self._voicemakeschema(i.id)
            self.voicedata[i] = (await server_config.get_server_config(i.id))['voice_creation_channel_id']
            
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
            
    def _voicemakeschema(self,gid):
        if gid not in list(self.voicedata.keys()):
            self.voicedata[str(gid)] = {"id":0,"channels":[]}
            print(self.voicedata)
            
    @voice.command("temphub")
    async def temphub(self, ctx,channel:discord.VoiceChannel):
        """Hub channel that creates a temporary voice channel for the user"""
        await ctx.defer(ephemeral=True)
        await server_config.set_server_voice_creation_channel(ctx.guild.id,channel.id)
        await ctx.send(f"Created temporary voice channel {channel.mention}.", ephemeral=True)
        self._voicemakeschema(str(ctx.guild.id))
        self.voicedata[str(ctx.guild.id)][id] = channel.id
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        print(member.name,before.channel.id if before.channel else "0",after.channel.id if after.channel else "0")
        if after.channel and after.channel.id == self.voicedata[str(member.guild.id)]:
            channel = await member.guild.create_voice_channel(name=f"{member.name}'s Voice", category=after.channel.category)
            await member.move_to(channel)
        if before.channel and before.channel.id in self.voicedata[str(member.guild.id)]['channels']:
            if after.channel and after.channel.id != before.channel.id:
                if before.channel.members == []:
                    await before.channel.delete()
                    self.voicedata[str(member.guild.id)]['channels'].remove(before.channel.id)
    
    async def _join(self,ctx):
        try:
            if ctx.author.voice is None:
                await ctx.send("You are not in a voice channel.", ephemeral=True)
                return
            channel = ctx.author.voice.channel
            await channel.connect()
        except:
            pass
        return channel
    
    async def _leave(self,ctx):
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
    async def leave(self,ctx):
        """Leave the current voice channel"""
        await self._leave(ctx)
        await ctx.send("Left the voice channel",ephemeral=True)
        
    @voice.group("youtube")
    async def yt(self,ctx):
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
        await ctx.send(embed=func.Embed().title("Playing 🎵").description(f"Playing **{player.title}**").footer(url).embed)
        
    @yt.command("stop")
    async def ytstop(self,ctx):
        """Stop playing"""
        client = ctx.voice_client
        client.stop()
        await ctx.send(embed=func.Embed().title("Stopped 🛑").embed)
async def setup(bot):
    await bot.add_cog(Voice(bot))
