import logging

from .logs import get_logger
from .luna import LunaBot

get_logger("discord", level=logging.INFO)



def main():
    """
    Initializes and runs the LunaBot instance.

    This function creates an instance of the LunaBot and starts it using the
    token from the bot's settings.
    """
    bot = LunaBot()
    bot.run(bot.settings.token, log_handler=None)
