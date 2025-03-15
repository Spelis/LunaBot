import discord
from discord.ext import commands
from discord import app_commands
import func
import datetime,pathlib,os
import database_conf
import requests

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
        if not args:
            await ctx.send(
                embed=func.Embed()
                .title("Help")
                .description("Select a category below to view commands")
                .embed,
                view=HelpView(self.bot, self),
            )
        else:
            c = self.bot.get_command(args)
            c.parents.reverse()
            emb = func.Embed().title(
                f"Help for {"group" if isinstance(c,commands.Group) else "command"} {args}"
            )
            if isinstance(c, commands.Group):
                emb.description = f"Group command containing {len(c.commands)} commands"
                for i in c.commands:
                    i.parents.reverse()
                    emb.embed.add_field(
                        name=f"{ctx.prefix}{' '.join(map(lambda x : x.name,i.parents))}{' ' if len(i.parents) > 0 else ''}{i.name}",
                        value=f"{i.signature}\n{i.help}",
                    )
            else:
                emb.embed.add_field(
                    name=f"{self.bot.command_prefix}{".".join(map(lambda x : x.name,c.parents))}{"." if len(c.parents) > 0 else ""}{c.name}",
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
                f"Uptime: {str(datetime.datetime.now()-ctx.bot.uptime)}"
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
            .section("Server Name", f"{ctx.guild.name}\n")
            .section("Members", f"{ctx.guild.member_count} total, {len(list(filter(lambda x: x.status not in [discord.Status.offline,discord.Status.invisible],ctx.guild.members)))} online")
            .section("Channels", f"{len(ctx.guild.text_channels)} text, {len(ctx.guild.voice_channels)} voice, {len(ctx.guild.channels)} total")
            .section("Owner", f"{ctx.guild.owner.display_name}")
            .footer(f"Created at {ctx.guild.created_at.strftime('%d/%m/%Y %H:%M:%S')}", f"{ctx.guild.icon.url}")
            .embed
        )
    @commands.hybrid_command("botinfo")
    async def botinfo(self, ctx):
        """Display bot info"""
        # This actually contains the directory of this file
        this = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
        main = func.get_main_directory(this).parent
        loc = func.count_files_and_lines(main)
        await ctx.send(
            embed=func.Embed()
            .title(f"{ctx.bot.user.display_name} Info")
            .section("Uptime", f"{datetime.datetime.now()-ctx.bot.uptime}") # crazy one liner below (who hurt me)
            .section("Servers", f"{len(ctx.bot.users)} unique members across {len(ctx.bot.guilds)} servers ({sum(list(map(lambda x: x.member_count,ctx.bot.guilds)))} total members)")
            .section("Commands", f"{len(ctx.bot.commands)} commands")
            .section("Lines", f"{loc[0]} Lines of code across {loc[1]} files")
            .thumbnail(ctx.bot.user.display_avatar.url)
            .footer(f"{ctx.bot.user.display_name}", f"{ctx.bot.user.display_avatar.url}")
            .embed
        )
        
    @commands.hybrid_command("sql")
    @func.is_developer()
    async def sql(self, ctx, *, query: str, commit=True):
        """Execute SQL query (Developer only)"""
        async with database_conf.aiosqlite.connect(database_conf.FILE) as conn:
            async with conn.cursor() as c:
                await c.execute(query)
                await ctx.send(embed=func.Embed().title("SQL Query").description(f"```{await c.fetchall()}```").embed,ephemeral=True)
                if commit:
                    await conn.commit()
                    
    @commands.hybrid_command(name="ip")
    @func.is_developer()
    async def getip(self,ctx):
        """Get the IP of the bot (Developer only) (Slash recommended)"""
        ip = requests.get("https://ipinfo.io/ip").text
        await ctx.send(embed=func.Embed().title("IP Address").description(f"```Pub Addr: {ip}\nLoc Addr: {func.getlocalip()}```").embed,ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
