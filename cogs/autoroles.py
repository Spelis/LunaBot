import discord
from discord.ext import commands

import conf
import func
from logs import Log


class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Auto Role Commands"
        self.emoji = "🎭"

    async def _ar_check_in_roles_list(self, guild_id: int, role_id: int) -> bool:
        return role_id in await conf.get_welcome_roles(guild_id)

    async def _ar_add_to_roles_list(self, guild_id: int, role_id: int) -> None:
        """Adds a role to the list of roles.
        Note that it doesn't check whether it's already added.

        Args:
            guild (int): ID of the Guild
            roleid (int): ID of the Role
        """
        roles = await conf.get_welcome_roles(guild_id)
        roles.append(role_id)
        new_roles = list(set(roles))
        await conf.set_welcome_roles(
            guild_id, new_roles
        )  # This handles serialization for us

    async def _ar_remove_from_roles_list(self, guild_id: int, role_id: int) -> None:
        """Removes a role from the list of roles.
        Note that it doesn't give a shit whether it's actually inside of the list.

        Args:
            guild (int): ID of the Guild
            roleid (int): ID of the Role
        """
        roles = await conf.get_welcome_roles(guild_id)
        roles.remove(role_id)
        await conf.set_welcome_roles(guild_id, roles)

    @commands.hybrid_group("ar")
    async def autorole(self, ctx):
        """Autorole commands"""
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self, ctx)

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
        if await self._ar_check_in_roles_list(ctx.guild.id, role.id):
            await self._ar_remove_from_roles_list(ctx.guild.id, role.id)
            await ctx.send("Role removed from the list of autoroles")
        else:
            await ctx.send("Role is not in the list of autoroles")

    @autorole.command("list")
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    async def autorole_list(self, ctx: commands.Context):
        """List all existing Autoroles"""
        role_list = await conf.get_welcome_roles(ctx.guild.id)
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
        role_ids = await conf.get_welcome_roles(guild.id)
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
    await bot.add_cog(Autorole(bot))
