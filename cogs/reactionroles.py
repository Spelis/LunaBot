import json
import traceback

import discord
from discord.ext import commands

import conf
import db_new
import func
from logs import Log


class ReactionRoles(commands.Cog):
    """Reaction Roles"""

    def __init__(self, bot):
        self.bot = bot
        self.description = "Reaction Role Commands"
        self.emoji = "🎭"

    async def cog_load(self):
        async with db_new.get_session() as session:
            for rr in await db_new.get_reaction_roles(session):
                rr: db_new.ReactionRole
                chan: discord.TextChannel = self.bot.get_channel(rr.ChannelID)
                # we dont need to do anything with this for now. just loading into discord.py cache or something
                msg = await chan.fetch_message(rr.MessageID)

    @commands.hybrid_group("reactrole", aliases=["rr", "rrole"])
    async def rr(self, ctx):
        """Reaction Roles, lets users react to a message and get a role in return."""
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self, ctx)

    @rr.command("add")
    @commands.has_guild_permissions(manage_roles=True)
    async def add(
        self, ctx, role: discord.Role, emoji: str
    ):  # TODO: add check to see if emoji provided is actually an emoji
        """Create new ReactRole"""
        async with db_new.get_session() as session:
            if ctx.message.reference is None:
                raise Exception(
                    "Needs to be a reply to an already existing message."
                )  # TODO: maybe make this its own exception?
            message: discord.Message = await ctx.channel.fetch_message(
                ctx.message.reference.message_id
            )  # make sure the shit is cached
            await db_new.create_reaction_role(
                session, ctx.guild.id, message.id, role.id, emoji
            )
            await message.add_reaction(emoji)
            await ctx.message.delete()
            await ctx.send(
                "Success", delete_after=3
            )  # write a simple success message and delete after a set time (3s)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        print("baller")  # prints 'baller' if the reaction actually gets registered.
        if user.id == self.bot.user.id:
            Log["reactroles"].info("Reaction is performed by me. Aborting.")
            return
        async with db_new.get_session() as session:
            rrole = await db_new.get_reaction_role_by_emoji_and_message(
                session, reaction.message.id, reaction.emoji
            )
            if rrole is not None:
                role = reaction.message.guild.get_role(rrole.RoleID)
                if role:
                    await user.add_roles(role)
                    Log["reactroles"].info(f"Added role {role.name} to {user.name}")
                else:
                    Log["reactroles"].error(f"Role {rrole.RoleID} not found")

    @commands.Cog.listener()
    async def on_reaction_remove(
        self, reaction: discord.Reaction, user: discord.Member
    ):
        if user.id == self.bot.user.id:
            Log["reactroles"].info("Reaction is performed by me. Aborting.")
            return
        async with db_new.get_session() as session:
            rrole = await db_new.get_reaction_role_by_emoji_and_message(
                session, reaction.message.id, reaction.emoji
            )
            if rrole is not None:
                role = reaction.message.guild.get_role(rrole.RoleID)
                if role:
                    await user.remove_roles(role)
                    Log["reactroles"].info(f"Removed role {role.name} from {user.name}")
                else:
                    Log["reactroles"].error(f"Role {rrole.RoleID} not found")

    @rr.command("remove")
    async def remove(self, ctx, message_id, emoji):
        """Remove a ReactRole"""
        async with db_new.get_session() as session:  # TODO: SOMEONE PLEASE CHANGE THIS
            rroleid = await db_new.get_reaction_role_by_emoji_and_message(
                session, message_id, emoji
            )
            await db_new.delete_reaction_role(session, rroleid.ReactRoleID)

    @rr.command("list")
    async def list(self, ctx, channel: discord.TextChannel):
        """List existing ReactRoles in a channel"""
        async with db_new.get_session() as session:
            reactlist = await db_new.get_reaction_roles_by_channel(session, channel.id)
            emb = (
                func.Embed()
                .title("Reaction Roles")
                .description("List of reaction roles setup:")
            )
            for i in reactlist:
                emb.section(
                    f"{i.ChannelID} > {i.MessageID} > {i.ReactRoleID}",
                    f"{i.Emoji} {await ctx.guild.fetch_role(i.RoleID)}",
                )
            await ctx.send(embed=emb.embed)


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
