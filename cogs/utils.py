import datetime
import os
import pathlib
import re
import subprocess
import sys

import aiosqlite
import discord
import requests
from discord import app_commands
from discord.ext import commands

import conf
import func


class HelpCategorySelection(discord.ui.Select):
    def __init__(self, bot, cog, cogs, zelf):
        options = []
        for k, v in cogs.items():
            if not hasattr(v, "hidden"):
                options.append(
                    discord.SelectOption(
                        label=k, description=v.description, emoji=v.emoji, value=k
                    )
                )

        super().__init__(placeholder="Select category", options=options)
        self.cog = cog
        self.cogs = cogs
        self.bot = bot
        self.parent = zelf

    async def callback(self, interaction: discord.Interaction):
        self.cog = self.cogs[interaction.data["values"][0]]
        embed = func.Embed().title(f"{self.cog.emoji} {self.cog.description}").embed
        for i in self.cog.get_commands():
            grouptxt = ""
            if isinstance(i, commands.Group):
                grouptxt = f"\nGroup command containing: {", ".join(["`"+i.name+(f" (G:{len(i.commands)})`" if isinstance(i,commands.Group) else "`") for i in i.commands])}"
            embed.add_field(
                name=f"{self.bot.command_prefix}{".".join(i.parents)}{"." if len(i.parents) > 0 else ""}{i.name}",
                value=f"{"`"+i.signature+"`" if i.signature else ""}\n{i.help}{grouptxt}",
            )
        await interaction.response.edit_message(embed=embed)


class HelpView(discord.ui.View):
    def __init__(self, bot, cog):
        super().__init__(timeout=None)
        self.dropdown = HelpCategorySelection(bot, cog, bot.cogs, self)
        self.add_item(self.dropdown)

    async def send_message(self):
        self.dropdown.message = await self.dropdown.channel.send(
            "Choose a Category!", view=self
        )


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Utility Commands"
        self.emoji = "🛠️"

    @commands.hybrid_command("ping")
    async def ping(self, ctx):
        """Pong!"""
        await ctx.send(
            embed=func.Embed().title(f"Pong | {round(self.bot.latency*1000)}ms").embed
        )

    async def _help(self, ctx, args: str | None = None):
        """Help command"""
        cog = self.bot.get_cog(args)
        if not args:
            await ctx.send(
                embed=func.Embed()
                .title("Help")
                .description("Select a category below to view commands")
                .embed,
                view=HelpView(self.bot, self),
            )
        elif cog is not None:
            embed = func.Embed().title(f"{cog.emoji} {cog.description}").embed
            for i in cog.get_commands():
                grouptxt = ""
                if isinstance(i, commands.Group):
                    grouptxt = f"\nGroup command containing: {", ".join(["`"+i.name+(f" (G:{len(i.commands)})`" if isinstance(i,commands.Group) else "`") for i in i.commands])}"
                embed.add_field(
                    name=f"{self.bot.command_prefix}{".".join(i.parents)}{"." if len(i.parents) > 0 else ""}{i.name}",
                    value=f"{"`"+i.signature+"`" if i.signature else ""}\n{i.help}{grouptxt}",
                )
            await ctx.send(embed=embed)
        else:
            c = self.bot.get_command(args)
            emb = func.Embed().title(
                f"Help for {"group" if isinstance(c,commands.Group) else "command"} {args}"
            )
            if isinstance(c, commands.Group):
                emb.description = f"Group command containing {len(c.commands)} commands"
                for i in c.commands:
                    emb.embed.add_field(
                        name=f"{ctx.prefix}{i.qualified_name}",
                        value=f"{i.signature}\n{i.help}",
                    )
            else:
                emb.embed.add_field(
                    name=f"{self.bot.command_prefix}{c.qualified_name}",
                    value=f"{"`"+c.signature+"`" if c.signature else ""}\n{c.help}",
                )
            await ctx.send(embed=emb.embed)

    @app_commands.command(name="help")
    async def slashhelp(
        self, interaction: discord.Interaction, args: str | None = None
    ):
        """Help command"""
        await self._help(await commands.Context.from_interaction(interaction), args)

    @commands.command(name="help", usage="command or group or None")
    async def help(self, ctx, *, args: str = ""):
        """Help command"""
        await self._help(ctx, args)

    @commands.hybrid_command("uptime")
    async def uptime(self, ctx):
        """Display uptime"""
        await ctx.send(
            embed=func.Embed()
            .title("Uptime")
            .description(
                f"```⏱️ {str(datetime.datetime.now()-ctx.bot.uptime)}```"
            )  # was unsure if f string use __repr__ or __str__
            .embed,
            ephemeral=True,
        )

    @commands.hybrid_command("serverinfo")
    async def serverinfo(self, ctx):
        """Display server info"""
        await ctx.send(
            embed=func.Embed()
            .title("Server Info")
            .section("Server Name", f"```{ctx.guild.name}```")
            .section("Server ID", f"```{ctx.guild.id}```")
            .section(
                "Members",
                f"```🧑‍🦲 {len(list(filter(lambda x: x.status not in [discord.Status.offline,discord.Status.invisible] and not x.bot,ctx.guild.members)))}/{len(list(filter(lambda x: not x.bot,ctx.guild.members)))}\n🤖 {len(list(filter(lambda x: x.status not in [discord.Status.offline,discord.Status.invisible] and x.bot,ctx.guild.members)))}/{len(list(filter(lambda x: x.bot,ctx.guild.members)))}```",
            )
            .section(
                "Channels",
                f"```💬 {len(ctx.guild.text_channels)}\n🗣️ {len(ctx.guild.voice_channels)}\n🫂 {len(ctx.guild.channels)} total```",
            )
            .section("Owner", ctx.guild.owner.mention)
            .footer(
                f"Created at {ctx.guild.created_at.strftime('%d/%m/%Y %H:%M:%S')}",
                f"{ctx.guild.icon.url}",
            )
            .thumbnail(ctx.guild.icon.url)
            .embed
        )

    @commands.hybrid_command("botinfo")
    async def botinfo(self, ctx):
        """Display bot info"""
        # This actually contains the directory of this file
        this = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
        main = func.get_main_directory(this).parent
        loc = func.count_files_and_lines(main)
        commit = (
            subprocess.check_output("git rev-parse HEAD", shell=True).decode().strip()
        )
        changes = str(
            sum(
                map(
                    lambda x: sum(map(int, x.split()[:2])) if x else 0,
                    re.sub(
                        r"( +|\t)",
                        " ",
                        subprocess.check_output(
                            "git diff --numstat", shell=True
                        ).decode(),
                    ).split("\n")[:-1],
                )
            )
        ).strip()
        await ctx.send(
            embed=func.Embed()
            .title(f"{ctx.bot.user.display_name} Info")
            .section(
                "Uptime",
                f"```⏱️ {str(datetime.datetime.now()-ctx.bot.uptime)}```",
            )
            .section(
                "Servers", f"```{len(ctx.bot.users)} 🧑‍🦲 {len(ctx.bot.guilds)} 🗄️```"
            )
            .section("Commands", f"```❕ {len(ctx.bot.commands)}```")
            .section("Lines", f"```🧑‍💻 {loc[0]} Lines across {loc[1]} files```")
            .section(
                "Version (Git Commit + Changes)",
                f"```\n{commit}{"+" if not changes.startswith("-") else ""}{changes}```",
            )  # get current git commit as "version" and count changes            .thumbnail(ctx.bot.user.display_avatar.url)
            .footer(
                f"{ctx.bot.user.display_name}", f"{ctx.bot.user.display_avatar.url}"
            )
            .embed
        )

    async def memberinfo(self, ctx, user: discord.Member = None):
        """Display member info"""
        statuses = {
            "online": "🟢",
            "offline": "⚫",
            "idle": "🟡",
            "dnd": "🔴",
        }
        if user is None:
            user = ctx.author
        await ctx.send(
            embed=func.Embed()
            .title(f"{user.display_name} Info")
            .section("ID", f"```🆔 {user.id}```")
            .section("Name", f"```👋 {user.display_name}```")
            .section("Tag", f"```📛 {user.name}```")
            .section(
                "Status",
                f"```{statuses.get(str(user.status))} {func.capitalize(user.status)}```",
            )
            .section(
                "Roles",
                f"```🗃️ {', '.join([i.name for i in user.roles if i.name != '@everyone'])}```",
            )
            .section(
                "Joined Server",
                f"```🗄️ {user.joined_at.strftime('%d/%m/%Y %H:%M:%S')}```",
            )
            .section(
                "Joined Discord",
                f"```🖥️ {user.created_at.strftime('%d/%m/%Y %H:%M:%S')}```",
            )
            .thumbnail(user.display_avatar.url)
            .footer(f"{user.display_name}", f"{user.display_avatar.url}")
            .embed
        )

    @commands.hybrid_command("userinfo")
    async def userinfo(self, ctx, user: discord.User = None):
        """Display user info"""
        if user.id in list(map(lambda x: x.id, ctx.guild.members)):
            await self.memberinfo(ctx, await ctx.guild.fetch_member(user.id))
            return
        if user is None:
            user = ctx.author
        await ctx.send(
            embed=func.Embed()
            .title(f"{user.display_name} Info")
            .section("ID", f"```🆔 {user.id}```")
            .section("Name", f"```👋 {user.display_name}```")
            .section("Tag", f"```📛 {user.name}```")
            .section(
                "Joined Discord",
                f"```🖥️ {user.created_at.strftime('%d/%m/%Y %H:%M:%S')}```",
            )
            .thumbnail(user.display_avatar.url)
            .footer(f"{user.display_name}", f"{user.display_avatar.url}")
            .embed
        )

    @commands.hybrid_command("sql")
    @func.is_developer()
    async def sql(self, ctx, *, query: str, commit=True):
        """Execute SQL query (Developer only)"""
        async with aiosqlite.connect("database.db") as conn:
            async with conn.cursor() as c:
                await c.execute(query)
                await ctx.send(
                    embed=func.Embed()
                    .title("SQL Query")
                    .description(f"```{await c.fetchall()}```")
                    .embed,
                    ephemeral=True,
                )
                if commit:
                    await conn.commit()

    @commands.hybrid_command("gitpull")
    @func.is_developer()
    async def gitpull(self, ctx):
        """Pull latest changes from git (Developer only)"""
        outp = subprocess.check_output("git pull", shell=True)
        await ctx.send(
            embed=func.Embed()
            .title("Git Pull")
            .description("```\n✅ Pulled latest changes from git```")
            .section("Output", f"```ansi\n{outp.decode()}```")
            .embed,
            ephemeral=True,
        )

    @commands.hybrid_command(name="ip")
    @func.is_developer()
    async def getip(self, ctx):
        """Get the IP of the bot (Developer only)"""
        ip = requests.get("https://ipinfo.io/ip").text
        chan = await ctx.author.create_dm()  # always DM user running the command
        await chan.send(
            embed=func.Embed()
            .title("IP Address")
            .description(f"```Pub Addr: {ip}\nLoc Addr: {func.getlocalip()}```")
            .embed
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
