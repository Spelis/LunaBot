import discord
import inspect
from discord.ext import commands
import yt_dlp
import pathlib
import spotipy,os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from logs import Log
import socket
import datetime

def getlocalip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def capitalize(s) -> str:
    s = str(s).lower()
    return " ".join(word[0].upper() + word[1:] for word in s.split(" ")) # nice oneliner

load_dotenv()
DEVELOPER_IDS = list(map(int,os.getenv("DEVELOPER_IDS", "0").split(",")))
Log['bootstrap'].info(f"Loaded developer IDs: {DEVELOPER_IDS}")

def td_format(td:datetime.timedelta):
    days = td.days
    hours,remainder = divmod(td.seconds, 3600)
    minutes,secs = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {secs}s"

class NotDev(commands.CheckFailure):
    pass

def is_developer():
    async def predicate(ctx):
        if ctx.author.id not in DEVELOPER_IDS:
            raise NotDev()
        return True
    return commands.check(predicate)

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": False,
    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
    "ignoreerrors": True,
}


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.uploader = data.get("uploader")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url):
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                data = ydl.extract_info(url, download=False)
                return cls(discord.FFmpegPCMAudio(data["url"]), data=data)
        except Exception as e:
            Log['functions'].info(e)
            return None
        
    @classmethod
    async def from_playlist(cls, url):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            data = ydl.extract_info(url, download=False)
            if 'entries' in data:
                return [({'title': entry.get('title'),
                        'url': entry.get('url'),
                        'uploader': entry.get('uploader')}
                        if entry is not None else {"title": "None", "url": "None", "uploader": "None"})
                        for entry in data['entries']]
            return []



class SpotifySource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.uploader = data.get("uploader")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url):
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
        track = sp.track(url)
        search_query = f"{track['name']} {track['artists'][0]['name']}"
        
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            data = ydl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            return cls(discord.FFmpegPCMAudio(data["url"]), data=track)

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
    try:
        # Try UTF-8 first (most common for code files)
        with open(file, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except UnicodeDecodeError:
        try:
            # Fall back to system default encoding with error handling
            with open(file, "r", errors="ignore") as f:
                return len(f.readlines())
        except Exception:
            # If all else fails, just count bytes and newlines
            try:
                with open(file, "rb") as f:
                    return f.read().count(b'\n') + 1
            except Exception:
                # Return 0 if we can't read the file at all
                return 0

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
