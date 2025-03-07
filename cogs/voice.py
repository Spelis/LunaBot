from discord.ext import commands
import discord
import func

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Voice chat shenanigans including music and sfx"
        self.emoji = "🎵"
        
        
async def setup(bot):
    if hasattr(bot, 'voice_client') and bot.voice_client is not None:
        await bot.add_cog(Voice(bot))
    else:
        print("Bot does not support voice.")
        raise commands.ExtensionError("Bot does not support voice.",name="voice")
