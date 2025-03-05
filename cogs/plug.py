from discord import Embed
from discord.ext import commands
import func


class Plugins(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Plugin Commands"
        self.emoji = "🔌"
        
    @commands.Cog.listener("on_command_error")
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        
        await ctx.send(
            embed=func.Embed()
            .title("Plugin ")
            .description(str(error))
            .embed,
            ephemeral=True,
        )

    @commands.hybrid_command("lplug", usage="plug")
    async def loadplug(self, ctx: commands.context.Context, plug):
        """Loads an Extension"""
        await self.bot.load_extension("cogs." + plug)
        await ctx.send(
            embed=func.Embed()
            .title("Loaded Extension")
            .description(f"{plug} has been successfully loaded.")
            .color(0xa6e3a1).embed,
            ephemeral=True,
        )
        await self.bot.tree.sync(guild=ctx.guild)

    @commands.hybrid_command("uplug", usage="plug")
    async def unloadplug(self, ctx, plug):
        """Unloads an Extension"""
        await self.bot.unload_extension("cogs." + plug)
        await ctx.send(
            embed=func.Embed()
            .title("Unloaded Extension")
            .description(f"{plug} has been successfully unloaded.")
            .color(0x45475a).embed,
            ephemeral=True,
        )
        await self.bot.tree.sync(guild=ctx.guild)

    @commands.hybrid_command("rplug", usage="plug")
    async def reloadplug(self, ctx, plug):
        """Reloads an Extension"""
        await self.bot.reload_extension("cogs." + plug)
        await ctx.send(
            embed=func.Embed()
            .title("Reloaded Extension")
            .description(f"{plug} has been successfully reloaded.")
            .color(0x89b4fa).embed,
            ephemeral=True,
        )
        await self.bot.tree.sync(guild=ctx.guild)


async def setup(bot: commands.Bot):
    await bot.add_cog(Plugins(bot))
