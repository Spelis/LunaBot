import discord
from discord.ext import commands

import conf
from logs import Log


class ReactionBot(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Reaction Commands"
        self.emoji = "👌"
        self.reactdata: dict[int, bool] = {}

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        for i in self.bot.guilds:
            await self.load_react_data_from_persistent(i.id)
        Log["reactions"].info(f"Loaded reaction data")

    async def load_react_data_from_persistent(self, guild_id: int):
        reaction = (await conf.get_server_config(guild_id)).get("reaction_toggle")
        if reaction is None:
            Log["reactions"].info(
                f"Reaction toggle unset, defaulting to True for guild {guild_id}."
            )
        else:
            self.reactdata[guild_id] = reaction

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            print(
                f"Presumably got a DM from {message.author.id} ({message.author.name}): {message.content}"
            )
            return
        if self.reactdata.get(message.guild.id, True):
            if "fr" in message.content.lower():
                await message.add_reaction("🇫🇷")
            if message.content.lower() == "ts pmo":
                await message.add_reaction("💔")
            if "🗿" in message.content.lower():
                await message.add_reaction("🗿")
            if "ok" == message.content.lower():
                await message.add_reaction("👍")
            if "good boy" == message.content.lower():
                await message.add_reaction("😊")
            if "this" == message.content.lower():
                # check if the message is a reply and if so react to the original message
                if message.reference and message.reference.resolved:
                    await message.reference.resolved.add_reaction(
                        discord.PartialEmoji(name="this", id=1346958257033445387)
                    )
                await message.delete()

    @commands.has_guild_permissions(manage_guild=True)
    @commands.hybrid_command("reacttoggle")
    async def toggle(self, ctx: commands.Context):
        """Toggle reactions on messages"""
        self.reactdata[ctx.guild.id] = not await conf.get_server_reaction_toggle(
            ctx.guild.id
        )
        await conf.set_server_reaction_toggle(
            ctx.guild.id, int(self.reactdata[ctx.guild.id])
        )
        await ctx.send(
            "Reactions are now "
            + ("enabled." if self.reactdata[ctx.guild.id] else "disabled.")
        )
        Log["reactions"].info(
            f"Toggled reactions for guild {ctx.guild.name} to {self.reactdata[ctx.guild.id]}"
        )


async def setup(bot):
    await bot.add_cog(ReactionBot(bot))
