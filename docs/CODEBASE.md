# Codebase Guide

So, you want to contribute to this project? or maybe you want to modify it for your own purposes?

Heres how to navigate the codebase.

> **This guide is Work in Progress!**

## main.py

The only purpose of the main file is to import the LunaBot class from the bot package and instantiate it.

Each instance of LunaBot comes with a static instance to the configuration file (`bot.settings`), where you can retrieve the token from.

More about the .env file <a href="#env">here</a>

## bot

This is the main package where all Luna code resides.

Unless you're making changes to how the modules are loaded or adding support for another database, you won't need to change anything in this package.

Features and discord.py cogs are in the `bot.modules` subdirectory.

## bot/modules

In Luna's codebase, cogs are always separated into extensions. They are loaded from the `bot.modules` package and contain all the commands and listeners. You can add your own cogs/extensions to the modules folder by following <a href="ADDING_COGS.md">this guide</a>.

## .env

<a id="env">

This is the `.env` file. It contains environment variables for the bot.

All supported env variables are defined in the `bot.config.Configuration` class (in pydantic format).

Here is a copy of the `example.env` file:

```env
# The token to log in with. This is the only mandatory value, everything else is optional.
LUNA_TOKEN=a.b.c
# The prefix to use for legacy commands
LUNA_PREFIX=!
# IDs of bot developers / instance owners (allow access to dev commands)
LUNA_DEVELOPER_IDS=[123,456,789]
# When both POSTGRES_URI and DB_FILE are defined, Luna will prefer the POSTGRES_URI.
LUNA_POSTGRES_URI=postgresql+asyncpg://<db_username>:<db_secret>@<db_host>:<db_port>/<db_name>
LUNA_DB_FILE=database.db
# When not set, MODULES_DIR defaults to the built-in bot.modules package as a POSIX path
# The code used to generate the string is in bot/modules/__init__.py as builtin_directory
LUNA_MODULES_DIR=bot/modules
# The ASCII banner to display when starting
LUNA_BANNER_FILE=bot/banner.txt
# Whether to display an ascii banner when starting
LUNA_SHOW_BANNER=true

# Logging options
LOGGING_DIRECTORY=logs
# The name of the log file. Since Luna uses a RotatingFileHandler, with a base name of "app.log", you would get "app.log", "app.log.1", "app.log.2", ... through to "app.log.5"
LOGGING_FILE_NAME=luna.log
# 10 MiB
LOGGING_MAX_BYTES=10485760
# Whether to set the Luna root logger to debug level
LOGGING_DEBUG=false
```
