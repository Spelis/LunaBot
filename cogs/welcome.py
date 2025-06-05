import json
import traceback

import discord
from discord.ext import commands

import conf
import db_new
import func
from logs import Log


class ChannelSelectDropdown(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Please select a channel", min_values=1, max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.data["values"][0]
        try:
            async with db_new.get_session() as session:
                await db_new.update_server_config(
                    session, interaction.guild.id, WelcomeChannelID=channel
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
            await func.cmd_group_fmt(self, ctx)

    @welcome.command("setup")
    async def _setup(self, ctx):
        """Setup the Welcome Bot"""
        await ctx.defer(ephemeral=True)
        existing_config = await conf.get_server_config(ctx.guild.id)
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
        async with db_new.get_session() as session:
            await db_new.update_server_config(
                session, ctx.guild.id, WelcomeChannelID=None
            )
        await ctx.send("Welcome bot has been reset.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        dmchan = await member.create_dm()
        await dmchan.send(  # send the user a message saying welcome
            f"Welcome to {member.guild.name} {member.mention}!\nThis server is powered by {self.bot.user.mention}. You can find commands by running `/help`.\n\nHave a great time!\n-# Oh yeah also, I'm open source! [github](<https://github.com/spelis/lunabot>)"
        )
        welcome_channel_id: int
        if member.guild.id in self.channel_cache:
            welcome_channel_id = self.channel_cache[member.guild.id]
        else:
            existing_config = await conf.get_server_config(member.guild.id)
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


class ReactionData:
    title: dict[int, str] = {}
    description: dict[int, str] = {}
    roles: dict[int, list[int, int]] = {}


async def setup(bot):
    await bot.add_cog(Welcomer(bot))
