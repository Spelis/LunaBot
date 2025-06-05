# Adding Cogs

All features in Luna are separated using Cogs, but worry not, for adding new cogs to the bot is easy.

## Steps

### Creating

- Create a new python file (or package) in the bot/modules folder.
- Import the necessary modules (<a href="#module-imports">Details</a>).
- Create a new class that inherits from `commands.Cog` (<a href="#creating-the-cog-class">Details</a>).
- Create an async function that initializes the cog. (<a href="#initializing-the-cog">Details</a>).
- Run the bot or load the cog with `/lplug {plugin name}`. (This might be changed in the future)
- Try out your new cog!

### Adding commands

- Define a new asynchronous method inside your cog
- Annotate it with `@commands.hybrid_command()`
- Done

## Details

### Module imports

<a id="module-imports">

You need some modules to make your cog work.

- `commands` from `discord.ext` (`from discord.ext import commands`) - The module that contains definitions of Cogs, Commands, and Command Groups.
- `discord` - The module that contains definitions of Discord objects.
- `LunaBot` from `bot.luna` - The module that contains the LunaBot class.
- `get_session` and quite possibly `init_db` from `bot.database` - The module that contains the object that can be used to get a DB session instance.

### Creating the cog class

<a id="creating-the-cog-class">

```python
class MyCog(commands.Cog):
    def __init__(self, bot: LunaBot):
        self.bot = bot
        self.description = "This is my cog" # Puts a description in the help command
        self.emoji = "🔥" # Puts an emoji in the help command
        # if self.hidden is defined, the cog will not be shown in the help command
```

### Initializing the Cog

<a id="initializing-the-cog">

For your extension to be recognized by discord.py, you must define an asynchronous setup function in your file.
If you made a package instead of a file, this function must be accessible from your `__init__.py`.

You can add as many cogs as you need in this function. If your extension defines models as well, you want to make sure they're imported and call init_db from `bot.database`.

```python
async def setup(bot):
    await bot.add_cog(MyCog(bot))
```
