import json
import traceback

import discord
from discord.ext import commands

import func
import conf as oldconf
import db_new as conf
from logs import Log


class ChannelSelectDropdown(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Please select a channel", min_values=1, max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.data["values"][0]
        try:
            await conf.Set.ServerWelcomeChannel(
                interaction.guild.id, channel
            )
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
            await interaction.response.send_message(
                "Something went wrong trying to set the welcome channel", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Successfully set welcome channel to <#" + str(channel) + ">",
            ephemeral=True,
        )


class SetupWizardChannelSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ChannelSelectDropdown())


class SetupWizardInitialPromptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please select a channel.",
            view=SetupWizardChannelSelectView(),
            ephemeral=True,
        )

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Setup cancelled.", ephemeral=True)


class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Join and Leave Announcements and Settings"
        self.emoji = "👋"
        self.channel_cache = {}

    @commands.hybrid_group("welcome")
    async def welcome(self, ctx):
        """Welcome Bot Commands"""
        if ctx.invoked_subcommand is None:
            command_list = ", ".join(
                [f"{c.name}" for c in self.welcome.commands]
                if len(self.welcome.commands) > 0
                else ["none"]
            )
            await ctx.send(
                embed=func.Embed()
                .title("You must choose a sub command!")
                .description("Available sub-commands: " + command_list)
                .embed,
                ephemeral=True,
            )

    @welcome.command("setup")
    async def _setup(self, ctx):
        """Setup the Welcome Bot"""
        await ctx.defer(ephemeral=True)
        await conf.Create.ServerConfig(ctx.guild.id)
        existing_config = await conf.Get.ServerConfig(ctx.guild.id)
        welcome_channel_id = existing_config.get("welcome_channel_id", None)
        if welcome_channel_id is not None:
            self.channel_cache[ctx.guild.id] = welcome_channel_id
            setup_embed = (
                func.Embed()
                .color(0x11111B)
                .title("Welcome Listener Setup")
                .description(
                    "**This server already has a welcome channel configured!**\nWould you like to re-run the setup wizard?"
                )
            )
        else:
            setup_embed = (
                func.Embed()
                .color(0x11111B)
                .title("Welcome Listener Setup")
                .description(
                    "The welcomer module doesn't appear to be setup on this server yet.\nWould you like to set it up now?"
                )
            )
        await ctx.send(
            embed=setup_embed.embed, view=SetupWizardInitialPromptView(), ephemeral=True
        )
        
    @welcome.command("reset")
    async def reset(self, ctx):
        """Reset the Welcome Bot"""
        await conf.Set.ServerWelcomeChannel(ctx.guild.id,None) # default value
        await ctx.send("Welcome bot has been reset.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        dmchan = await member.create_dm()
        await dmchan.send( # send the user a message saying welcome
            f"Welcome to {member.guild.name} {member.mention}!\nThis server is powered by {self.bot.user.mention}. You can find commands by running `/help`.\n\nHave a great time!"
        )
        welcome_channel_id: int
        if member.guild.id in self.channel_cache:
            welcome_channel_id = self.channel_cache[member.guild.id]
        else:
            await conf.Create.ServerConfig(member.guild.id)
            existing_config = await conf.Get.ServerConfig(member.guild.id)
            welcome_channel_id = existing_config.get("welcome_channel_id", None)
            if welcome_channel_id is not None:
                self.channel_cache[member.guild.id] = welcome_channel_id
            else:
                # No welcome channel is set up
                print("Welcome channel is not set up")
                return
        welcome_channel = member.guild.get_channel_or_thread(welcome_channel_id)
        if welcome_channel is None:
            # Welcome channel is set up, but is invalid
            # We don't invalidate cache, since that'd just make us fetch it from the database every time someone joins.
            # It's faster to just check against a dict.
            print("Welcome channel is invalid")
            return
        await welcome_channel.send(
            embed=func.Embed()
            .title(f"Welcome to {member.guild.name}!")
            .description(f"Welcome {member.mention}!")
            .thumbnail(member.avatar.url)
            .embed
        )

class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Auto Role Commands"
        self.emoji = "🎭"
        
    async def _ar_check_in_roles_list(self, guild_id: int, role_id: int) -> bool:
        return role_id in await oldconf.get_welcome_roles(guild_id)

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
                

class ReactionData:
    title:dict[int,str] = {}
    description:dict[int,str] = {}
    roles:dict[int,list[int,int]] = {}

class ReactionRoles(commands.Cog):
    """Reaction Roles"""
    def __init__(self, bot):
        self.bot = bot
        self.description = "Reaction Role Commands"
        self.emoji = "🎭"
        
    async def on_load(self):
        pass

async def setup(bot):
    await bot.add_cog(Welcomer(bot))
    await bot.add_cog(Autorole(bot))
    rr = ReactionRoles(bot)
    await bot.add_cog(rr)
    await rr.on_load()
