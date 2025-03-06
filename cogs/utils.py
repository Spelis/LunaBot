import discord
from discord.ext import commands
from discord import app_commands
import func


class HelpCategorySelection(discord.ui.Select):
    def __init__(self, bot, cog, cogs,zelf):
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
        embed = func.Embed().title(self.cog.description).embed
        for i in self.cog.get_commands():
            grouptxt = ""
            if isinstance(i,commands.Group):
                grouptxt = f"\nGroup command containing {len(i.commands)} commands"
                self.parent.add_item(RedirectHelpButton(i,self.parent))
            embed.add_field(
                name=f"{self.bot.command_prefix}{".".join(i.parents)}{"." if len(i.parents) > 0 else ""}{i.name}",
                value=f"{"`"+i.signature+"`" if i.signature else ""}\n{i.help}{grouptxt}",
            )
        await interaction.response.edit_message(embed=embed)
        
class RedirectHelpButton(discord.ui.Button):
    def __init__(self, group,zelf):
        super().__init__(label=f"view help for {group}", emoji="🔗")
        self.group = group
        self.parent:Utils = zelf
        
    async def callback(self,interaction: discord.Interaction):
        ctx = commands.Context.from_interaction(interaction)
        await self.parent._help(ctx,self.group)


class HelpView(discord.ui.View):
    def __init__(self, bot, cog):
        super().__init__(timeout=None)
        self.dropdown = HelpCategorySelection(bot, cog, bot.cogs,self)
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
                .description("This is the help command")
                .embed,
                view=HelpView(self.bot, self),
            )
        else:
            await ctx.send(
                embed=func.Embed()
                .title(f"Help for {args}")
                .description("working on it cuh")
                .embed
            )

    @app_commands.command(name="help")
    async def slashhelp(
        self, interaction: discord.Interaction, args: str | None = None
    ):
        """Help command"""
        await self._help(await commands.Context.from_interaction(interaction), args)

    @commands.command(name="help",usage="command or group or None")
    async def help(self, ctx, *, args: str = ""):
        """Help command"""
        await self._help(ctx, args)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
