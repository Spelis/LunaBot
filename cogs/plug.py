from discord.ext import commands
import func
import os

class Plugins(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Plugin Commands"
        self.emoji = "🔌"

    @commands.hybrid_command("lplug", usage="plug")
    async def loadplug(self, ctx: commands.context.Context, plug):
        """Loads an Extension"""
        await self.bot.load_extension("cogs." + plug)
        await ctx.send(
            embed=func.Embed()
            .title("Loaded Extension")
            .description(f"{plug} has been successfully loaded.")
            .color(0xA6E3A1)
            .embed,
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
            .color(0x45475A)
            .embed,
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
            .color(0x89B4FA)
            .embed,
            ephemeral=True,
        )
        await self.bot.tree.sync(guild=ctx.guild)

    @commands.hybrid_command("raplug", usage="plug")
    async def reloadallplug(self, ctx):
        """Reloads all Extensions"""
        emb = (
            func.Embed()
            .title("Reloading Extensions...")
            .description("Shouldn't take long...")
            .color(0xFAB387)
        )
        errcount = 0
        for extension in self.bot.extensions.copy():
            try:
                await self.bot.reload_extension(extension)
                emb.embed.add_field(
                    name=extension + " :white_check_mark:", value="", inline=False
                )
            except:
                emb.embed.add_field(name=extension + " :x:", value="", inline=False)
                errcount += 1
        emb.description(
            f"Completed reload of all extensions with {errcount} error{"s" if errcount != 1 else ""}"
        )
        await ctx.send(embed=emb.embed)

    @commands.hybrid_command("plug")
    async def plugins(self, ctx):
        """List all Plugins"""
        # await ctx.defer()
        emb = (
            func.Embed().title("Plugins").description("List of Plugins").color(0x89B4FA)
        )
        for extensionraw in os.listdir("cogs"):
            if extensionraw == "__pycache__":
                continue
            extension = "".join(extensionraw.split(".")[:-1])
            print(extension)
            if "cogs."+extension in self.bot.extensions:
                results = func.analyze_extension("cogs."+extension)
                ncogs = 0
                ncommands = 0
                for cog_data in results:
                    ncogs += 1
                    ncommands += cog_data["command_count"]
                emb.embed.add_field(
                    name=extension,
                    value=f"{ncommands} command{"s" if ncommands != 1 else ""} across {ncogs} cog{"s" if ncommands != 1 else ""}",
                    inline=False,
                )
            else:
                emb.embed.add_field(
                    name=extension, value="Not loaded", inline=False
                )
        await ctx.send(embed=emb.embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Plugins(bot))
