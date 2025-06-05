import discord
from discord.ext import commands

from bot.luna import LunaBot
from bot.database import get_session

from .services import ExampleService


class HelloWorld(commands.Cog):
    def __init__(self, bot: LunaBot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping", usage="ping", description='Responds with "Pong!"'
    )
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _ping(self, ctx: commands.Context):
        await ctx.reply("Pong!", ephemeral=True)

    @commands.hybrid_group(
        "example",
        usage="example (list|create <name>|delete <id>|update <id> <name>)",
        description="Example commands",
    )
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def example(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply("Please specify a subcommand.", ephemeral=True)

    @example.command("list", usage="example list", description="List all examples")
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def example_list(self, ctx: commands.Context):
        async with get_session() as session:
            svc = ExampleService.from_session(session)
            names = list(map(lambda model: f"{model.name} ({model.id})", await svc.get_all()))
        await ctx.reply("Examples: " + "\n".join(names), ephemeral=True)

    @example.command(
        "create", usage="example create <name>", description="Create a new example"
    )
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def example_create(self, ctx: commands.Context, name: str):
        async with get_session() as session:
            svc = ExampleService.from_session(session)
            model = await svc.create(name)
            model_id = model.id
        await ctx.reply(
            f"Created example with name {name} (id: {model_id})", ephemeral=True
        )

    @example.command(
        "delete", usage="example delete <id>", description="Delete an example"
    )
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def example_delete(self, ctx: commands.Context, id: int):
        async with get_session() as session:
            svc = ExampleService.from_session(session)
            model = await svc.get(id)
            if model is None:
                await ctx.reply(f"Example with id {id} not found", ephemeral=True)
                return
            await svc.delete(model)
        await ctx.reply(f"Deleted example with id {id}", ephemeral=True)

    @example.command(
        "update", usage="example update <id> <name>", description="Update an example"
    )
    @commands.has_permissions(send_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def example_update(self, ctx: commands.Context, id: int, name: str):
        async with get_session() as session:
            svc = ExampleService.from_session(session)
            model = await svc.get(id)
            if model is None:
                await ctx.reply(f"Example with id {id} not found", ephemeral=True)
                return
            model.name = name
            model = await svc.update(model)
        await ctx.reply(f"Updated example with id {id} to name {name}", ephemeral=True)
