import discord
from discord.ext import commands
import func
import asyncio

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Admin Commands"
        self.emoji = "🛡️"
        
    @commands.hybrid_command("purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self,ctx:commands.context.Context,amount:int):
        await ctx.channel.purge(limit=amount)

async def setup(bot):
    await bot.add_cog(Admin(bot))
