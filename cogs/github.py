from re import A
import discord
from discord.ext import commands
from datetime import datetime,timezone
import func
import requests

class GitHub(commands.Cog):
    def __init__(self,bot):
        self.description = "GitHub API Interactions"
        self.emoji = "😺"
        
    @commands.hybrid_group("github",aliases=["gh"])
    async def gh(self,ctx):
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self,ctx)
    
    @gh.group("user")
    async def ghuser(self,ctx):
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self,ctx)
            
    @ghuser.command("info")
    async def ghuserinfo(self,ctx,username):
        r = requests.get(f"https://api.github.com/users/{username}")
        j = r.json()
        await ctx.send(
            embed=func.Embed()
            .title(f"Info on {j['login']}")
            .section("Name",f"```\n🧑‍🦲 {j['name']}```")
            .section("Location", f"```\n📍 {j['location']}```")
            .section("Following | Followers",f"```\n↗️ {j['following']} | ↙️ {j['followers']}```")
            .section("Repos | Gists",f"```\n🗄️ {j['public_repos']} | {j['public_gists']}```")
            .section("Bio",f"```\n{j['bio']}```")
            .thumbnail(j['avatar_url'])
            .url(j['html_url'])
            .embed
        )
    @ghuser.command("repos")
    async def ghuserrepos(self,ctx,username):
        r = requests.get(f"https://api.github.com/users/{username}/repos")
        j = r.json()
        await ctx.send("someone make pagination for this please :3")
        
    @gh.group("repo")
    async def ghrepo(self,ctx):
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self,ctx)
            
    @ghrepo.command("info")
    async def ghrepoinfo(self,ctx,user,repo):
        r = requests.get(f"https://api.github.com/repos/{user}/{repo}")
        j = r.json()
        
    
async def setup(bot):
    await bot.add_cog(GitHub(bot))
