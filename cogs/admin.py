import discord
from discord.ext import commands
import func
import asyncio
from logs import Log

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Admin Commands"
        self.emoji = "🛡️"
        
    @commands.hybrid_command("purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self,ctx:commands.context.Context,amount:int):
        """Deletes a specified amount of messages from the channel"""
        await ctx.channel.purge(limit=amount)
        Log['admin'].info(f"{ctx.author.name} purged {amount} messages from {ctx.channel.name}")
        
    @commands.hybrid_command("ban")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Bans a member from the server"""
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member.mention} because {reason}")
        Log['admin'].info(f"{ctx.author.name} banned {member.name} because {reason}")
            
    @commands.hybrid_command("uban")
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self,ctx:commands.context.Context,member:discord.User):
        """Unbans a member from the server"""
        await ctx.guild.unban(member)
        await ctx.send(f"Unbanned {member.mention}")
        Log['admin'].info(f"{ctx.author.name} unbanned {member.name}")
        
    @commands.hybrid_command("kick")
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Kicks a member from the server"""
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member.mention} because {reason}")
        Log['admin'].info(f"{ctx.author.name} kicked {member.name} because {reason}")
    
    @commands.hybrid_command("mute")
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Toggles mute for a member in the server"""
        muted = not member.voice.mute if member.voice else False
        await member.edit(mute=muted,reason=reason)
        status = "Muted" if muted else "Unmuted"
        await ctx.send(f"{status} {member.mention} because {reason}")
        Log['admin'].info(f"{ctx.author.name} muted {member.name} because {reason}")
    
    @commands.hybrid_command("deafen")
    @commands.has_guild_permissions(deafen_members=True)
    async def deafen(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Toggles deafen for a member in the server"""
        deafened = not member.voice.deaf if member.voice else False
        await member.edit(deafen=deafened,reason=reason)
        status = "Deafened" if deafened else "Undeafened"
        await ctx.send(f"{status} {member.mention} because {reason}")
        Log['admin'].info(f"{ctx.author.name} deafened {member.name} because {reason}")

    @commands.hybrid_group("vc")
    async def vc(self,ctx):
        """Voice Channel Commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command")
            
    @vc.command("move")
    @commands.has_guild_permissions(move_members=True)
    async def move(self,ctx:commands.context.Context,member:discord.Member,channel:discord.VoiceChannel):
        """Moves a member to a voice channel"""
        await member.move_to(channel)
        await ctx.send(f"Moved {member.mention} to {channel.mention}")
        Log['admin'].info(f"{ctx.author.name} moved {member.name} to {channel.name}")
        
    @vc.command("kick")
    @commands.has_guild_permissions(move_members=True)
    async def kick(self,ctx:commands.context.Context,member:discord.Member):
        """Kicks a member from the voice channel"""
        chan = member.voice.channel
        await member.move_to(None)
        await ctx.send(f"Kicked {member.mention} from {chan.mention}")
        Log['admin'].info(f"{ctx.author.name} kicked {member.name} from {chan.name}")


async def setup(bot):
    await bot.add_cog(Admin(bot))
