from typing import Any

import discord
from discord.ext import commands
from sqlmodel import text

from bot import luna_api
from bot.database import engine
from bot.luna import LunaBot


class Developer(commands.Cog):
    def __init__(self, bot: LunaBot):
        self.bot = bot
        # Whether the user prefers to be cussed out.
        self.user_preference: dict[int, bool] = {380987045008506880: True}

    async def _insult_user_if_no_subcommand_specified(self, ctx: commands.Context):
        """
        Checks if the user specified a subcommand. If not, sends a helpful error
        message to the user. The message is slightly different depending on the
        user's preference.

        Args:
            ctx (commands.Context): The current context.

        Returns:
            None
        """
        if ctx.invoked_subcommand is None:
            await ctx.reply(
                (
                    "You need to specify a subcommand, dumbass! Obviously."
                    if self.user_preference.get(ctx.author.id, False)
                    else "Please specify a subcommand."
                ),
                ephemeral=True,
            )

    @commands.hybrid_group(
        name="dev", usage="dev", description="Commands for LunaBot developers"
    )
    @commands.cooldown(1, 2, commands.BucketType.user)
    @luna_api.permission.luna_developer_only()
    async def root(self, ctx: commands.Context):
        await self._insult_user_if_no_subcommand_specified(ctx)

    @root.command(
        name="insult",
        usage="dev insult",
        description="Toggles whether the bot should insult you or not.",
    )
    async def _insult(self, ctx: commands.Context):
        self.user_preference[ctx.author.id] = not self.user_preference.get(
            ctx.author.id, False
        )
        await ctx.reply(
            (
                "You will now be insulted when you improperly use a legacy command."
                if self.user_preference[ctx.author.id]
                else "You will no longer insulted when you improperly use a legacy command."
            ),
            ephemeral=True,
        )

    @root.command(
        name="reload",
        usage="dev reload",
        description="Reloads the entire bot (from the core up).",
    )
    async def _reload(self, ctx):
        # TODO: Implement
        # I was going to add this in the initial developer cog commit, but I realized we will need a more complicated watchdog to actually do what the command is supposed to do.
        await ctx.reply("Not yet implemented", ephemeral=True)

    @root.command(
        name="shutdown",
        usage="dev shutdown",
        description="Shuts down the bot.",
    )
    async def _shutdown(self, ctx):
        await ctx.reply("Shutting down...", ephemeral=True)
        await self.bot.close()

    @root.command("eval", usage="dev eval <code>")
    async def _eval(self, ctx: commands.Context, *, code: str):
        result: None | Any = None
        try:
            result = eval(code, globals(), locals())
        except Exception as e:
            await ctx.reply(f"Failed to evaluate code: {e}", ephemeral=True)
        else:
            await ctx.reply(f"Result: {result}", ephemeral=True)

    @root.command("exec", usage="dev exec <code>")
    async def _exec(self, ctx: commands.Context, *, code: str):
        try:
            exec(code, globals(), locals())
        except Exception as e:
            await ctx.reply(f"Failed to execute code: {e}", ephemeral=True)
        else:
            await ctx.reply("Successfully executed code", ephemeral=True)

    @root.command("sql", usage="dev sql <query>")
    async def _sql(self, ctx: commands.Context, *, query: str):
        #! THIS IS IMPLEMENTATION-SPECIFIC TO SQLMODEL
        result: None | Any = None
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text(query))
                result = "\n".join([str(row) for row in result])
        except Exception as e:
            await ctx.reply(f"Failed to execute SQL query: {e}", ephemeral=True)
        else:
            await ctx.reply(
                "Successfully executed SQL query\n```sql\n"
                + (result or "\n")
                + "\n```",
                ephemeral=True,
            )

    @root.group("module")
    async def module_root(self, ctx: commands.Context):
        await self._insult_user_if_no_subcommand_specified(ctx)

    @module_root.command(
        name="list",
        usage="dev module list",
        description="Lists all loaded modules.",
    )
    async def _module_list(self, ctx: commands.Context):
        module_names = list(self.bot.extensions.keys())
        available_module_names = self.bot.find_available_extensions()
        modules = [
            (
                f"{name}"
                + (
                    " (loaded)"
                    if name in module_names
                    else (
                        " (available)"
                        if name in available_module_names
                        else " (unknown)"
                    )
                )
            )
            for name in available_module_names
        ]
        # This sorts the list such that the loaded modules are at the top
        modules = list(
            sorted(
                modules,
                key=lambda x: x.upper() if x.endswith("(loaded)") else x.lower(),
            )
        )
        await ctx.reply(
            "Luna's Modules\n" + "\n".join(modules),
            ephemeral=True,
        )

    @module_root.command(
        name="load",
        usage="dev module load <module>",
        description="Loads a module.",
    )
    async def _module_load(self, ctx: commands.Context, module: str):
        try:
            await self.bot.load_extension(module)
        except Exception as e:
            await ctx.reply(f"Failed to load module '{module}': {e}", ephemeral=True)
        else:
            await ctx.reply(f"Successfully loaded module '{module}'", ephemeral=True)

    @module_root.command(
        name="unload",
        usage="dev module unload <module>",
        description="Unloads a module.",
    )
    async def _module_unload(self, ctx: commands.Context, module: str):
        try:
            await self.bot.unload_extension(module)
        except Exception as e:
            await ctx.reply(f"Failed to unload module '{module}': {e}", ephemeral=True)
        else:
            await ctx.reply(f"Successfully unloaded module '{module}'", ephemeral=True)

    @module_root.command(
        name="reload",
        usage="dev module reload <module>",
        description="Reloads a module.",
    )
    async def _module_reload(self, ctx: commands.Context, module: str):
        try:
            await self.bot.reload_extension(module)
        except Exception as e:
            await ctx.reply(f"Failed to reload module '{module}': {e}", ephemeral=True)
        else:
            await ctx.reply(f"Successfully reloaded module '{module}'", ephemeral=True)
