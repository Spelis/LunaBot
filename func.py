import discord
import json
import inspect
from discord.ext import commands
import yt_dlp, os,pathlib

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
}


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            data = ydl.extract_info(url, download=False)
            return cls(discord.FFmpegPCMAudio(data["url"]), data=data)


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

    def section(self, label: str, value: str, inline: bool = True):
        self.embed.add_field(name=label, value=value, inline=inline)
        return self

    def thumbnail(self, url: str = ""):
        self.embed.set_thumbnail(url=url)
        return self


# Thanks HyScript for this amazing set of functions to count lines :)
# (Almost did it myself but hyscript said no)

def get_main_directory(initial_dir: pathlib.Path):
    this = initial_dir
    main = None
    while main is None:
        if this.joinpath("main.py").is_file():
            main = this.joinpath("main.py")
        elif this.root == str(this):
            print("Root reached, no main.py found")
            main = initial_dir
        else:
            this = this.parent
    return main

def count_lines(file: pathlib.Path) -> int:
    """
    Count the number of lines in a file

    Args:
        file (pathlib.Path): the file to count lines in

    Returns:
        int: the number of lines in the file
    """
    with open(file, "r") as f:
        return len(f.readlines())

def count_files_and_lines(dir: pathlib.Path) -> tuple[int, int]:
    """Go through every file in the directory and count it.
    If we reach a directory that is not in the ignored_dirs list, recursively call this function

    Args:
        dir (pathlib.Path): The initial directory to count from
    
    Returns:
        tuple(int, int): (lines_of_code, files)
    """
    ignored_dirs = [".git", ".venv", "venv", ".vscode"]
    lines_of_code = 0
    files = 0
    for f in dir.iterdir():
        if f.is_dir():
            if f.name not in ignored_dirs:
                sub_lines_of_code, sub_files = count_files_and_lines(f)
                lines_of_code += sub_lines_of_code
                files += sub_files
        else:
            if f.name.endswith(".py"):
                lines_of_code += count_lines(f)
                files += 1
    return (lines_of_code, files)


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
            if (
                inspect.isclass(obj)
                and issubclass(obj, commands.Cog)
                and obj != commands.Cog
            ):
                cogs.append(obj)

        return cogs
    except ImportError:
        raise ValueError(f"Could not import module: {module_path}")


def get_commands_in_cog(cog_class):
    """Count commands in a Cog class."""
    comm = []
    for name, attr in inspect.getmembers(cog_class):
        if isinstance(attr, commands.Command) or isinstance(attr, commands.Group):
            comm.append(attr)
    return comm


def analyze_extension(extension_path):
    """Analyze an extension and report on its cogs and commands."""
    try:
        # Get all cogs from the extension
        cogs = get_cogs_from_module(extension_path)

        # Analyze each cog
        results = []
        for cog in cogs:
            comm = get_commands_in_cog(cog)
            results.append(
                {
                    "name": cog.__name__,
                    "command_count": len(comm),
                    "commands": [cmd.name for cmd in comm],
                }
            )

        return results
    except Exception as e:
        raise RuntimeError(f"Error analyzing extension: {str(e)}")
