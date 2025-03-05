import discord
from discord.ext import commands
import func


class HelpCategorySelection(discord.ui.Select):
    def __init__(self,bot, cog, cogs):
        options = []
        for k, v in cogs.items():
            if not hasattr(v,"hidden"):
                options.append(discord.SelectOption(label=k, description=v.description, emoji=v.emoji,value=k))
            
        super().__init__(placeholder="Select category", options=options)
        self.cog = cog
        self.cogs = cogs
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        self.cog = self.cogs[interaction.data['values'][0]]
        embed = func.Embed().title(self.cog.description).embed
        for i in self.cog.get_commands():
            embed.add_field(
                name=f"{self.bot.command_prefix}{".".join(i.parents)}{"." if len(i.parents) > 0 else ""}{i.name}",
                value=f"{"`" + i.usage + "`" if i.usage else ""}\n{i.help}"
            )
        await interaction.response.edit_message(
            embed=embed
        )


class HelpView(discord.ui.View):
    def __init__(self,bot, cog):
        super().__init__(timeout=None)
        self.dropdown = HelpCategorySelection(bot,cog, bot.cogs)
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

    @commands.hybrid_command("help")
    async def help(self, ctx, args: str | None = None):
        """Help command"""
        if not args:
            await ctx.send(
                embed=func.Embed()
                .title("Help")
                .description("This is the help command")
                .embed,
                view=HelpView(self.bot,self),
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
