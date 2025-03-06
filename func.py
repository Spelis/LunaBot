import discord
import json
import inspect
from discord.ext import commands


class Embed:
    def __init__(self):
        self.embed = discord.Embed(color=0xCBA6F7)

    def color(self, color: int = 0x000000):
        self.embed.color = color
        return self

    def title(self, title: str = ""):
        self.embed.title = title
        return self

    def description(self, description: str = ""):
        self.embed.description = description
        return self

    def url(self, url: str = ""):
        self.embed.url = url
        return self

    def author(self, name: str, url: str = "", icon_url: str = ""):
        self.embed.set_author(name, url=url, icon_url=icon_url)
        return self

    def footer(self, text: str = "", icon_url: str = ""):
        self.embed.set_footer(text=text, icon_url=icon_url)
        return self

    def thumbnail(self, url: str = ""):
        self.embed.set_thumbnail(url=url)
        return self

    def section(self, label: str, value: str, inline: bool = False):
        self.embed.add_field(name=label, value=value, inline=inline)
        return self

    def thumbnail(self, url: str = ""):
        self.embed.set_thumbnail(url=url)
        return self

# bro just let me see the amount of cogs in a module 😭

def get_cogs_from_module(module_path):
    """Discover all Cog classes in a module."""
    try:
        # Import the module dynamically
        import importlib
        module = importlib.import_module(module_path)
        
        # Find all Cog subclasses in the module
        cogs = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, commands.Cog) and obj != commands.Cog:
                cogs.append(obj)
                
        return cogs
    except ImportError:
        raise ValueError(f"Could not import module: {module_path}")

def get_commands_in_cog(cog_class):
    """Count commands in a Cog class."""
    commands = []
    for name, attr in inspect.getmembers(cog_class):
        if isinstance(attr, commands.Command) or isinstance(attr, commands.Group):
            commands.append(attr)
    return commands

def analyze_extension(extension_path):
    """Analyze an extension and report on its cogs and commands."""
    try:
        # Get all cogs from the extension
        cogs = get_cogs_from_module(extension_path)
        
        # Analyze each cog
        results = []
        for cog in cogs:
            commands = get_commands_in_cog(cog)
            results.append({
                'name': cog.__name__,
                'command_count': len(commands),
                'commands': [cmd.name for cmd in commands]
            })
            
        return results
    except Exception as e:
        raise RuntimeError(f"Error analyzing extension: {str(e)}")
