import discord
import json


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
