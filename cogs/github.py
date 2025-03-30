from datetime import datetime, timezone
from re import A

import discord
import requests
from discord.ext import commands

import func


class GitHub(commands.Cog):
    def __init__(self, bot):
        self.description = "GitHub API Interactions"
        self.emoji = "😺"
        self.bot = bot

    @commands.hybrid_group("github", aliases=["gh"])
    async def gh(self, ctx):
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self, ctx)

    @gh.group("user")
    async def ghuser(self, ctx):
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self, ctx)

    @ghuser.command("info")
    async def ghuserinfo(self, ctx, username):
        r = requests.get(f"https://api.github.com/users/{username}")
        j = r.json()
        dt = datetime.strptime(j["created_at"], r"%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        td = datetime.now(timezone.utc) - dt
        await ctx.send(
            embed=func.Embed()
            .title(f"Info on {j['login']}")
            .section("Name", f"```\n🧑‍🦲 {j['name']}```")
            .section("Location", f"```\n📍 {j['location']}```")
            .section(
                "Following | Followers",
                f"```\n↗️ {j['following']} | ↙️ {j['followers']}```",
            )
            .section(
                "Repos | Gists", f"```\n🗄️ {j['public_repos']} | {j['public_gists']}```"
            )
            .section("Bio", f"```\n{j['bio']}```")
            .section(
                "Account age", f"```{str(td)}\n({dt.strftime("%Y-%m-%d %H:%M:%S")})```"
            )
            .thumbnail(j["avatar_url"])
            .url(j["html_url"])
            .embed
        )

    @ghuser.command("repos")
    async def ghuserrepos(self, ctx, username, page):
        r = requests.get(f"https://api.github.com/users/{username}/repos?page={page}")
        j = r.json()[0]

    @gh.group("repo")
    async def ghrepo(self, ctx):
        if ctx.invoked_subcommand is None:
            await func.cmd_group_fmt(self, ctx)

    @ghrepo.command("info")
    async def ghrepoinfo(self, ctx, user, repo):
        r = requests.get(f"https://api.github.com/repos/{user}/{repo}")
        j = r.json()
        created_at = datetime.now(timezone.utc) - datetime.strptime(
            j["created_at"], r"%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        updated_at = datetime.now(timezone.utc) - datetime.strptime(
            j["updated_at"], r"%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        pushed_at = datetime.now(timezone.utc) - datetime.strptime(
            j["pushed_at"], r"%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        await ctx.send(
            embed=func.Embed()
            .title(f"{"🔒 " if j['archived'] else ""}{j['full_name']}")
            .description(j["description"])
            .section("Language", j["language"])
            .section("Created", created_at)
            .section("Updated", updated_at)
            .section("Pushed", pushed_at)
            .section("Topics", j["topics"])
            .url(j["html_url"])
            .embed
        )

    @ghrepo.command("langchart")
    async def ghrepolangchart(self, ctx, user, repo):
        r = requests.get(f"https://api.github.com/repos/{user}/{repo}/languages")
        j = r.json()
        # just making sure its sorted
        j = dict(sorted(j.items(), key=lambda item: item[1]))
        total = sum(j.values())
        other = sum(value for value in j.values() if (value / total) * 100 < 0.1)
        j = {k: v for k, v in j.items() if (v / total) * 100 >= 0.1}
        if other > 0:
            j["Other"] = other
        perc = ";".join(map(lambda x: f"{x[0]}, {(x[1]/total)*100}", list(j.items())))
        await ctx.invoke(self.bot.get_command("piechart"), data=perc)


async def setup(bot):
    await bot.add_cog(GitHub(bot))
