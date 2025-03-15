Adding new cogs to the bot is easy.

# Steps:

## Creating
- Create a new python file in the cogs folder.
- Import the necessary modules (<a href="#module-imports">Details</a>).
- Create a new class that inherits from `commands.Cog` (<a href="#creating-the-cog-class">Details</a>).
- Create an async function that initializes the cog. (<a href="#initializing-the-cog">Details</a>).
- Run the bot or load the cog with `/lplug {plugin name}`.
- Try out your new cog!

## Adding commands

# Details

## Module imports
You need some modules to make your cog work.
- `discord.ext.commands` (`from discord.ext import commands`) - The module that contains definitions of Cogs, Commands, and Command Groups.
- `discord.app_commands` (`from discord import app_commands`) - The module that contains definitions of Slash Commands. (You will rarely need this)
- `discord` - The module that contains definitions of Discord objects.
- `func` - Some functions Luna uses to make things easier.
- `database_conf` - The module that contains some database functions.

## Creating the cog class

```python
class MyCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.description = "This is my cog" # Puts a description in the help command
        self.emoji = "🔥" # Puts an emoji in the help command
        # if self.hidden is defined, the cog will not be shown in the help command
```

## Initializing the Cog
```python
async def setup(bot):
    await bot.add_cog(MyCog(bot))
```
