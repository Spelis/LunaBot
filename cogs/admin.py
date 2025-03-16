import base64
import json
import random

import discord
from discord.ext import commands

import database_conf
import func
from logs import Log

global channelattrs
channelattrs = {
    "text": [
        "changed_roles",
        "default_auto_archive_duration",
        "default_thread_slowmode_delay",
        "name",
        "nsfw",
        "overwrites",
        "permissions_synced",
        "slowmode_delay",
        "topic",
    ],
    "voice": [
        "bitrate",
        "changed_roles",
        "channel_flags",
        "default_auto_archive_duration",
        "default_thread_slowmode_delay",
        "name",
        "nsfw",
        "overwrites",
        "permissions_synced",
        "user_limit",
    ],
    # add more later idk
}


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Admin Commands"
        self.emoji = "🛡️"

    @commands.hybrid_command("purge")
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Deletes a specified amount of messages from the channel"""
        await ctx.channel.purge(limit=amount)
        await ctx.send(
            embed=func.Embed()
            .title("Purged!")
            .description(f"```🗑️ {amount}```")
            .color(0xA6E3A1)
            .embed
        )
        Log["admin"].info(
            f"{ctx.author.name} purged {amount} messages from {ctx.channel.name}"
        )

    @commands.hybrid_command("ban")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "Empty Reason",
    ):
        """Bans a member from the server"""
        await member.ban(reason=reason)
        await ctx.send(
            embed=func.Embed()
            .title("Banned!")
            .description(f"```🔨 {member.display_name}\n❔ {reason}```")
            .color(0xF38BA8)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} banned {member.name} because {reason}")

    @commands.hybrid_command("uban")
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, member: discord.User):
        """Unbans a member from the server"""
        await ctx.guild.unban(member)
        await ctx.send(
            embed=func.Embed()
            .title("Unbanned!")
            .description(f"```🔓 {member.display_name}```")
            .color(0xA6E3A1)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} unbanned {member.name}")

    @commands.hybrid_command("kick")
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "Empty Reason",
    ):
        """Kicks a member from the server"""
        await member.kick(reason=reason)
        await ctx.send(
            embed=func.Embed()
            .title("Kicked!")
            .description(f"```👢 {member.display_name}\n❔ {reason}```")
            .color(0xF38BA8)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} kicked {member.name} because {reason}")

    @commands.hybrid_command("mute")
    @commands.has_guild_permissions(mute_members=True)
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "Empty Reason",
    ):
        """Toggles mute for a member in the server"""
        muted = not member.voice.mute if member.voice else False
        await member.edit(mute=muted, reason=reason)
        status = "Muted" if muted else "Unmuted"
        await ctx.send(
            embed=func.Embed()
            .title(f"{status}!")
            .description(f"```🔇 {member.display_name}\n❔ {reason}```")
            .color(0xF9E2AF)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} muted {member.name} because {reason}")

    @commands.hybrid_command("deafen")
    @commands.has_guild_permissions(deafen_members=True)
    async def deafen(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "Empty Reason",
    ):
        """Toggles deafen for a member in the server"""
        deafened = not member.voice.deaf if member.voice else False
        await member.edit(deafen=deafened, reason=reason)
        status = "Deafened" if deafened else "Undeafened"
        await ctx.send(
            embed=func.Embed()
            .title(f"{status}!")
            .description(f"```🔕 {member.display_name}\n❔ {reason}```")
            .color(0xF9E2AF)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} deafened {member.name} because {reason}")

    @commands.hybrid_command("vcmove")
    @commands.has_guild_permissions(move_members=True)
    async def vcmove(
        self,
        ctx: commands.Context,
        member: discord.Member,
        channel: discord.VoiceChannel,
    ):
        """Moves a member to a voice channel"""
        await member.move_to(channel)
        await ctx.send(
            embed=func.Embed()
            .title("Moved!")
            .description(f"```➡️ {member.display_name} to {channel.name}```")
            .color(0x89B4FA)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} moved {member.name} to {channel.name}")

    @commands.hybrid_command("vckick")
    @commands.has_guild_permissions(move_members=True)
    async def vckick(self, ctx: commands.Context, member: discord.Member):
        """Kicks a member from the voice channel"""
        chan = member.voice.channel
        await member.move_to(None)
        await ctx.send(
            embed=func.Embed()
            .title("Kicked from VC!")
            .description(f"```⛔ {member.display_name} from {chan.name}```")
            .color(0xF38BA8)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} kicked {member.name} from {chan.name}")

    @commands.hybrid_command("slowmode")
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """Sets the slowmode for the channel"""
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(
            embed=func.Embed()
            .title("Slowmode Set!")
            .description(f"```⏱️ {seconds} seconds```")
            .color(0x89B4FA)
            .embed
        )
        Log["admin"].info(
            f"{ctx.author.name} set slowmode to {seconds} seconds in {ctx.channel.name}"
        )

    @commands.hybrid_command("vclimit")
    @commands.has_guild_permissions(manage_channels=True)
    async def vclimit(
        self, ctx: commands.Context, channel: discord.VoiceChannel, limit: int
    ):
        """Sets the user limit for a voice channel"""
        await channel.edit(user_limit=limit)
        await ctx.send(
            embed=func.Embed()
            .title("Limit Set!")
            .description(f"```👥 {limit} users in {channel.name}```")
            .color(0x89B4FA)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} set limit to {limit} in {channel.name}")

    @commands.hybrid_group("clip")
    async def clip(self, ctx: commands.Context):
        """Clipboard commands"""
        pass

    @clip.command("copy")
    async def clipcopy(self, ctx: commands.Context, channel: discord.TextChannel):
        """Copies a channel to the clipboard"""
        if isinstance(channel, discord.TextChannel):
            type = "text"
        elif isinstance(channel, discord.VoiceChannel):
            type = "voice"
        obj = {"type": type}
        for i in channelattrs[type]:
            obj[i] = getattr(channel, i)
        pick = json.dumps(obj)
        pick = base64.b64encode(pick.encode()).decode()
        await ctx.send(
            embed=func.Embed()
            .title("Copied!")
            .description(f"```📥 {channel.name}\n📋 {pick}```")
            .color(0x89B4FA)
            .embed
        )

    @clip.command("paste")
    @commands.has_guild_permissions(manage_channels=True)
    async def clippaste(self, ctx: commands.Context, obj: str):
        """Pastes a channel from the clipboard"""
        pick = base64.b64decode(obj).decode()
        obj = json.loads(pick)
        if obj["type"] == "text":
            channel = await ctx.guild.create_text_channel(
                name=obj["name"] + str(random.randint(100000, 999999)),
                topic=obj["topic"],
                nsfw=obj["nsfw"],
                slowmode_delay=obj["slowmode_delay"],
                overwrites=obj["overwrites"],
            )
        elif obj["type"] == "voice":
            channel = await ctx.guild.create_voice_channel(
                name=obj["name"] + str(random.randint(100000, 999999)),
                user_limit=obj["user_limit"],
                bitrate=obj["bitrate"],
                overwrites=obj["overwrites"],
            )
        await channel.send(
            f"Created channel from #{obj['name']} by {ctx.author.display_name}"
        )
        await ctx.send(
            embed=func.Embed()
            .title("Pasted!")
            .description(f"```📤 {channel.name}```")
            .color(0x89B4FA)
            .embed
        )

    @commands.hybrid_group("chan")
    async def chan(self, ctx: commands.Context):
        """Channel commands"""
        pass

    @chan.command("create")
    @commands.has_guild_permissions(manage_channels=True)
    async def chancreate(
        self,
        ctx: commands.Context,
        type: str,
        name: str,
        category: discord.CategoryChannel = None,
    ):
        """Creates a channel"""
        if type == "text":
            channel = await ctx.guild.create_text_channel(name=name, category=category)
        elif type == "voice":
            channel = await ctx.guild.create_voice_channel(name=name, category=category)
        elif type == "category":
            channel = await ctx.guild.create_category(name=name)
        elif type == "stage":
            channel = await ctx.guild.create_stage_channel(name=name, category=category)
        elif type == "forum":
            channel = await ctx.guild.create_forum_channel(name=name, category=category)
        elif type == "announcement":
            channel = await ctx.guild.create_announcement_channel(
                name=name, category=category
            )
        await ctx.send(
            embed=func.Embed()
            .title("Channel Created!")
            .description(f"```📝 {name}```")
            .color(0xA6E3A1)
            .embed
        )
        Log["admin"].info(f"{ctx.author.name} created {channel.name}")

    @chan.command("invite")
    @commands.has_guild_permissions(create_instant_invite=True)
    async def chaninvite(self, ctx: commands.Context):
        """Creates an invite for a channel"""
        msg = await ctx.send("Creating invite...")
        channel = ctx.channel
        invite = await channel.create_invite(max_age=0, max_uses=0)
        await msg.edit(
            content="",
            embed=func.Embed()
            .title("Invite Created!")
            .description(f"```🔗 {invite.url}```")
            .color(0x89B4FA)
            .embed,
        )

    async def _ar_check_in_roles_list(self, guild_id: int, role_id: int) -> bool:
        return role_id in await database_conf.get_welcome_roles(guild_id)

    async def _ar_add_to_roles_list(self, guild_id: int, role_id: int) -> None:
        """Adds a role to the list of roles.
        Note that it doesn't check whether it's already added.

        Args:
            guild (int): ID of the Guild
            roleid (int): ID of the Role
        """
        roles = await database_conf.get_welcome_roles(guild_id)
        roles.append(role_id)
        new_roles = list(set(roles))
        await database_conf.set_welcome_roles(
            guild_id, new_roles
        )  # This handles serialization for us

    async def _ar_remove_from_roles_list(self, guild_id: int, role_id: int) -> None:
        """Removes a role from the list of roles.
        Note that it doesn't give a shit whether it's actually inside of the list.

        Args:
            guild (int): ID of the Guild
            roleid (int): ID of the Role
        """
        roles = await database_conf.get_welcome_roles(guild_id)
        roles.remove(role_id)
        await database_conf.set_welcome_roles(guild_id, roles)

    @commands.hybrid_group("ar")
    async def autorole(self, ctx):
        """Autorole commands"""
        if ctx.invoked_subcommand is None:
            try:
                await ctx.send_help(ctx.command)
            except Exception as e:
                await ctx.reply("You must specify a sub command!", ephemeral=True)

    @autorole.command("add")
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    async def autorole_add(self, ctx: commands.Context, role: discord.Role):
        """Adds an autorole"""
        if not await self._ar_check_in_roles_list(ctx.guild.id, role.id):
            await self._ar_add_to_roles_list(ctx.guild.id, role.id)
            await ctx.send("Role added to the list of autoroles")
        else:
            await ctx.send("Role is already in the list of autoroles")

    @autorole.command("remove")
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    async def autorole_remove(self, ctx: commands.Context, role: discord.Role):
        """Removes an autorole"""
        if await self._ar_check_in_roleslist(ctx.guild.id, role.id):
            await self._ar_remove_from_roleslist(ctx.guild.id, role.id)
            await ctx.send("Role removed from the list of autoroles")
        else:
            await ctx.send("Role is not in the list of autoroles")

    @autorole.command("list")
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    async def autorole_list(self, ctx: commands.Context):
        role_list = await database_conf.get_welcome_roles(ctx.guild.id)
        embed = func.Embed().title("Autoroles").color(0x89B4FA).description()
        for i in role_list:
            role = ctx.guild.get_role(i)
            if role is None:
                try:
                    role = await ctx.guild.fetch_role(i)
                except discord.NotFound:
                    Log["admin"].warning(
                        f"Role {i} not found in {ctx.guild.name}, removing it from the list!"
                    )
                    await self._ar_remove_from_roles_list(ctx.guild.id, i)
                    continue
            embed.description(f"{embed.embed.description}\n- {role.mention}")
        await ctx.send(embed=embed.embed)

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member):
        guild = member.guild
        # Default config creation is now handled in the actual getter it self
        # if not await database_conf.get_server_config(guild.id):
        #     await database_conf.create_default_server_config(guild.id)
        role_ids = await database_conf.get_welcome_roles(guild.id)
        if role_ids:
            for role in role_ids:
                role = guild.get_role(role)
                if role is None:
                    try:
                        role = await guild.fetch_role(role)
                    except discord.NotFound:
                        Log["admin"].warning(
                            f"Role {role} not found in {guild.name}, removing it from the list!"
                        )
                        await self._ar_remove_from_roles_list(guild.id, role)
                        continue
                await member.add_roles(role)


async def setup(bot):
    await bot.add_cog(Admin(bot))
