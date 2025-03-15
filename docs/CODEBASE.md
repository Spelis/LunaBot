So, you want to contribute to this project? or maybe you want to modify it for your own purposes?

Heres how to navigate the codebase.

## main.py
This is the main file. It defines the bot and runs it. also loads the .env file for environment variables, which contains the bot token, prefix, and other stuff.

This file also handles the bot's presence in the function `async def update_presence()`.

More about the .env file <a href="#env">here</a>

## Cogs

Cogs are like extensions. They are loaded from the cogs folder and contains the commands and listeners. You can add your own cogs/extensions to the cogs folder by following <a href="ADDING_COGS.md">this guide</a>.

## .env
This is the .env file. It contains environment variables for the bot.

Variables the bot uses:

- `TOKEN`: The bot token. REQUIRED
- `PREFIX`: The prefix for the bot.
- `DEVELOPER_IDS`: The developer IDs for the bot. Used for protected commands that only trusted people should use.
- `PICKY`: Whether or not the bot should load all <a href="#cogs">cogs</a> on startup or not.
- `USETEX`: Toggle for using native LaTeX rendering or the one provided by matplotlib.
- `LOGGER_DEBUG`: Debug logging for the bot.
