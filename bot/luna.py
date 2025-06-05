import importlib
import logging
from datetime import datetime, timezone
from logging import Logger

import discord
from discord.ext import commands

from .config import Settings, settings
from .logs import get_logger


class LunaBot(commands.Bot):
    logger: Logger
    settings: Settings = settings

    start_time: datetime

    def __init__(self):
        super().__init__(
            command_prefix=self.settings.prefix,
            help_command=None,
            intents=discord.Intents.all(),
        )
        self.logger = (
            get_logger("luna")
            if settings.logger_settings.debug
            else get_logger("luna", level=logging.DEBUG)
        )
        if self.settings.show_banner:
            from .banner import get_banner_text

            if banner_text := get_banner_text():
                self.logger.info("\n" + banner_text)

    def run(self, token: str, *, reconnect: bool = True, log_handler: logging.Handler | None = ..., log_formatter: logging.Formatter = ..., log_level: int = ..., root_logger: bool = False) -> None:  # type: ignore
        self.start_time = datetime.now(timezone.utc)
        return super().run(
            token,
            reconnect=reconnect,
            log_handler=log_handler,
            log_formatter=log_formatter,
            log_level=log_level,
            root_logger=root_logger,
        )

    async def on_ready(self):
        self.logger.info(
            "Logged in as %s (%d)",
            self.user.name if self.user else "?",
            self.user.id if self.user else 0,
        )

    def _package_contains_setup_function(self, import_name: str) -> bool:
        try:
            module = importlib.import_module(import_name)
            return hasattr(module, "setup")
        except ModuleNotFoundError:
            return False

    async def setup_hook(self) -> None:
        extensions: list[str] = []
        for path in self.settings.modules_directory.iterdir():
            if path.name.startswith("__"):
                continue
            if path.is_file() and path.suffix == ".py":
                import_name: str = (
                    self.settings.modules_import_prefix
                    + "."
                    + path.name.removesuffix(".py")
                )
                if self._package_contains_setup_function(import_name):
                    extensions.append(import_name)
            elif path.is_dir():
                import_name: str = self.settings.modules_import_prefix + "." + path.name
                if self._package_contains_setup_function(import_name):
                    extensions.append(import_name)
        self.logger.info(
            "Discovered %d extensions: %s", len(extensions), ", ".join(extensions)
        )
        errors: int = 0
        for extension in extensions:
            try:
                await self.load_extension(extension)
            except commands.ExtensionError:
                errors += 1
            else:
                self.logger.info(f"Successfully loaded extension {extension}")
        self.logger.info(
            f"Successfully loaded {len(extensions) - errors}/{len(extensions)} extensions"
        )

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        self.logger.debug("Attempting to load extension '%s'", name)
        try:
            return await super().load_extension(name, package=package)
        except commands.ExtensionNotFound as e:
            self.logger.error("Extension '%s' not found", name)
            raise e
        except commands.ExtensionAlreadyLoaded as e:
            self.logger.warning("Extension '%s' is already loaded", name)
            raise e
        except commands.NoEntryPointError as e:
            self.logger.error("Extension '%s' does not have a setup function", name)
            raise e
        except commands.ExtensionFailed as e:
            self.logger.error(f"Failed to load extension '{name}': {e}", exc_info=e)
            raise e
        finally:
            self.logger.debug("Successfully loaded extension '%s'", name)

    async def unload_extension(self, name: str, *, package: str | None = None) -> None:
        self.logger.debug("Attempting to unload extension '%s'", name)
        try:
            await super().unload_extension(name, package=package)
            self.logger.debug("Successfully unloaded extension '%s'", name)
        except commands.ExtensionNotFound as e:
            self.logger.error("Extension '%s' not found", name)
            raise e
        except commands.ExtensionNotLoaded as e:
            self.logger.warning("Extension '%s' not loaded", name)
            raise e

    async def reload_extension(self, name: str, *, package: str | None = None) -> None:
        self.logger.debug("Attempting to reload extension '%s'", name)
        await super().reload_extension(name, package=package)
        self.logger.debug("Successfully reloaded extension '%s'", name)
