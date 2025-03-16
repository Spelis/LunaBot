import json
from math import e
import discord
from discord.ext import commands
import database_conf
import func
import asyncio
from logs import Log
import random
import base64
from enum import Enum

global channelattrs
channelattrs = {
    "text": ['changed_roles','default_auto_archive_duration','default_thread_slowmode_delay','name','nsfw','overwrites','permissions_synced','slowmode_delay','topic'],
    "voice": ['bitrate','changed_roles','channel_flags','default_auto_archive_duration','default_thread_slowmode_delay','name','nsfw','overwrites','permissions_synced','user_limit'],
    # add more later idk
}

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Admin Commands"
        self.emoji = "🛡️"
        
    @commands.hybrid_command("purge")
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self,ctx:commands.context.Context,amount:int):
        """Deletes a specified amount of messages from the channel"""
        await ctx.channel.purge(limit=amount)
        await ctx.send(embed=func.Embed().title("Purged!").description(f"```🗑️ {amount}```").color(0xa6e3a1).embed)
        Log['admin'].info(f"{ctx.author.name} purged {amount} messages from {ctx.channel.name}")
        
    @commands.hybrid_command("ban")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Bans a member from the server"""
        await member.ban(reason=reason)
        await ctx.send(embed=func.Embed().title("Banned!").description(f"```🔨 {member.display_name}\n❔ {reason}```").color(0xf38ba8).embed)
        Log['admin'].info(f"{ctx.author.name} banned {member.name} because {reason}")
            
    @commands.hybrid_command("uban")
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self,ctx:commands.context.Context,member:discord.User):
        """Unbans a member from the server"""
        await ctx.guild.unban(member)
        await ctx.send(embed=func.Embed().title("Unbanned!").description(f"```🔓 {member.display_name}```").color(0xa6e3a1).embed)
        Log['admin'].info(f"{ctx.author.name} unbanned {member.name}")
        
    @commands.hybrid_command("kick")
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Kicks a member from the server"""
        await member.kick(reason=reason)
        await ctx.send(embed=func.Embed().title("Kicked!").description(f"```👢 {member.display_name}\n❔ {reason}```").color(0xf38ba8).embed)
        Log['admin'].info(f"{ctx.author.name} kicked {member.name} because {reason}")
    
    @commands.hybrid_command("mute")
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Toggles mute for a member in the server"""
        muted = not member.voice.mute if member.voice else False
        await member.edit(mute=muted,reason=reason)
        status = "Muted" if muted else "Unmuted"
        await ctx.send(embed=func.Embed().title(f"{status}!").description(f"```🔇 {member.display_name}\n❔ {reason}```").color(0xf9e2af).embed)
        Log['admin'].info(f"{ctx.author.name} muted {member.name} because {reason}")
    
    @commands.hybrid_command("deafen")
    @commands.has_guild_permissions(deafen_members=True)
    async def deafen(self,ctx:commands.context.Context,member:discord.Member,reason:str="Empty Reason"):
        """Toggles deafen for a member in the server"""
        deafened = not member.voice.deaf if member.voice else False
        await member.edit(deafen=deafened,reason=reason)
        status = "Deafened" if deafened else "Undeafened"
        await ctx.send(embed=func.Embed().title(f"{status}!").description(f"```🔕 {member.display_name}\n❔ {reason}```").color(0xf9e2af).embed)
        Log['admin'].info(f"{ctx.author.name} deafened {member.name} because {reason}")

    @commands.hybrid_command("vcmove")
    @commands.has_guild_permissions(move_members=True)
    async def vcmove(self,ctx:commands.context.Context,member:discord.Member,channel:discord.VoiceChannel):
        """Moves a member to a voice channel"""
        await member.move_to(channel)
        await ctx.send(embed=func.Embed().title("Moved!").description(f"```➡️ {member.display_name} to {channel.name}```").color(0x89b4fa).embed)
        Log['admin'].info(f"{ctx.author.name} moved {member.name} to {channel.name}")
        
    @commands.hybrid_command("vckick")
    @commands.has_guild_permissions(move_members=True)
    async def vckick(self,ctx:commands.context.Context,member:discord.Member):
        """Kicks a member from the voice channel"""
        chan = member.voice.channel
        await member.move_to(None)
        await ctx.send(embed=func.Embed().title("Kicked from VC!").description(f"```⛔ {member.display_name} from {chan.name}```").color(0xf38ba8).embed)
        Log['admin'].info(f"{ctx.author.name} kicked {member.name} from {chan.name}")
        
    @commands.hybrid_command("slowmode")
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self,ctx:commands.context.Context,seconds:int):
        """Sets the slowmode for the channel"""
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=func.Embed().title("Slowmode Set!").description(f"```⏱️ {seconds} seconds```").color(0x89b4fa).embed)
        Log['admin'].info(f"{ctx.author.name} set slowmode to {seconds} seconds in {ctx.channel.name}")
        
    @commands.hybrid_command("vclimit")
    @commands.has_guild_permissions(manage_channels=True)
    async def vclimit(self,ctx:commands.context.Context,channel:discord.VoiceChannel,limit:int):
        """Sets the user limit for a voice channel"""
        await channel.edit(user_limit=limit)
        await ctx.send(embed=func.Embed().title("Limit Set!").description(f"```👥 {limit} users in {channel.name}```").color(0x89b4fa).embed)
        Log['admin'].info(f"{ctx.author.name} set limit to {limit} in {channel.name}")
    
    @commands.hybrid_group("clip")
    async def clip(self,ctx:commands.context.Context):
        """Clipboard commands"""
        pass
    
    @clip.command("copy")
    async def clipcopy(self,ctx:commands.context.Context,channel:discord.TextChannel):
        """Copies a channel to the clipboard"""
        if isinstance(channel, discord.TextChannel):
            type = 'text'
        elif isinstance(channel, discord.VoiceChannel):
            type = 'voice'
        obj = {"type":type}
        for i in channelattrs[type]:
            obj[i] = getattr(channel,i)
        pick = json.dumps(obj)
        pick = base64.b64encode(pick.encode()).decode()
        await ctx.send(embed=func.Embed().title("Copied!").description(f"```📥 {channel.name}\n📋 {pick}```").color(0x89b4fa).embed)
        
    @clip.command("paste")
    @commands.has_guild_permissions(manage_channels=True)
    async def clippaste(self,ctx:commands.context.Context,obj:str):
        """Pastes a channel from the clipboard"""
        pick = base64.b64decode(obj).decode()
        obj = json.loads(pick)
        if obj['type'] == 'text':
            channel = await ctx.guild.create_text_channel(name=obj['name'] + str(random.randint(100000,999999)),topic=obj['topic'],nsfw=obj['nsfw'],slowmode_delay=obj['slowmode_delay'],overwrites=obj['overwrites'])
        elif obj['type'] == 'voice':
            channel = await ctx.guild.create_voice_channel(name=obj['name'] + str(random.randint(100000,999999)),user_limit=obj['user_limit'],bitrate=obj['bitrate'],overwrites=obj['overwrites'])
        await channel.send(f"Created channel from #{obj['name']} by {ctx.author.display_name}")
        await ctx.send(embed=func.Embed().title("Pasted!").description(f"```📤 {channel.name}```").color(0x89b4fa).embed)

    @commands.hybrid_group("chan")
    async def chan(self,ctx:commands.context.Context):
        """Channel commands"""
        pass

    @chan.command("create")
    @commands.has_guild_permissions(manage_channels=True)
    async def chancreate(self,ctx:commands.context.Context,type:str,name:str,category:discord.CategoryChannel=None):
        """Creates a channel"""
        if type == "text":
            channel = await ctx.guild.create_text_channel(name=name,category=category)
        elif type == "voice":
            channel = await ctx.guild.create_voice_channel(name=name,category=category)
        elif type == "category":
            channel = await ctx.guild.create_category(name=name)
        elif type == "stage":
            channel = await ctx.guild.create_stage_channel(name=name,category=category)
        elif type == "forum":
            channel = await ctx.guild.create_forum_channel(name=name,category=category)
        elif type == "announcement":
            channel = await ctx.guild.create_announcement_channel(name=name,category=category)
        await ctx.send(embed=func.Embed().title("Channel Created!").description(f"```📝 {name}```").color(0xa6e3a1).embed)
        Log['admin'].info(f"{ctx.author.name} created {channel.name}")
        
    @chan.command("invite")
    @commands.has_guild_permissions(create_instant_invite=True)
    async def chaninvite(self,ctx:commands.context.Context):
        """Creates an invite for a channel"""
        msg = await ctx.send("Creating invite...")
        channel = ctx.channel
        invite = await channel.create_invite(max_age=0,max_uses=0)
        await msg.edit(content="",embed=func.Embed().title("Invite Created!").description(f"```🔗 {invite.url}```").color(0x89b4fa).embed)
        
    async def _ar_check_in_roleslist(self,guild:int,roleid:int):
        jsonstr = await database_conf.get_welcomeroles(guild)
        jsonobj = json.loads(jsonstr)
        if roleid in jsonobj:
            return True
        else:
            return False
        
    async def _ar_add_to_roleslist(self,guild,roleid:int):
        jsonstr = await database_conf.get_welcomeroles(guild)
        jsonobj = json.loads(jsonstr)
        jsonobj.append(roleid)
        jsonstr = json.dumps(jsonobj)
        await database_conf.set_welcomeroles(guild,jsonstr)
        return True
    
    async def _ar_remove_from_roleslist(self,guild,roleid:int):
        jsonstr = await database_conf.get_welcomeroles(guild)
        jsonobj = json.loads(jsonstr)
        jsonobj.remove(roleid)
        jsonstr = json.dumps(jsonobj)
        await database_conf.set_welcomeroles(guild,jsonstr)
        return True
        
        
    @commands.hybrid_group("ar")
    async def autorole(self,ctx):
        """Autorole commands"""
        pass
    
    @autorole.command("add")
    @commands.has_guild_permissions(manage_roles=True,manage_guild=True)
    async def autorole_add(self,ctx:commands.context.Context,role:discord.Role):
        """Adds an autorole"""
        if not await self._ar_check_in_roleslist(ctx.guild.id,role.id):
            await self._ar_add_to_roleslist(ctx.guild.id,role.id)
            
    @autorole.command("remove")
    @commands.has_guild_permissions(manage_roles=True,manage_guild=True)
    async def autorole_remove(self,ctx:commands.context.Context,role:discord.Role):
        """Removes an autorole"""
        if await self._ar_check_in_roleslist(ctx.guild.id,role.id):
            await self._ar_remove_from_roleslist(ctx.guild.id,role.id)
            
    @autorole.command("list")
    @commands.has_guild_permissions(manage_roles=True,manage_guild=True)
    async def autorole_list(self,ctx:commands.context.Context):
        """Lists all autoroles"""
        jsonstr = await database_conf.get_welcomeroles(ctx.guild.id)
        jsonobj = json.loads(jsonstr)
        embed = func.Embed().title("Autoroles").color(0x89b4fa)
        for i in jsonobj:
            role = ctx.guild.get_role(i)
            embed.section(f"{role.mention}")
        await ctx.send(embed=embed.embed)
        
    @commands.Cog.listener("on_member_join")
    async def on_member_join(self,member):
        guild = member.guild
        if not await database_conf.get_server_config(guild.id):
            await database_conf.create_default_server_config(guild.id)
        welcomeroles = await database_conf.get_welcomeroles(guild)
        if welcomeroles:
            for role in welcomeroles:
                role = guild.get_role(role)
                await member.add_roles(role)
        

async def setup(bot):
    await bot.add_cog(Admin(bot))
