import discord
from discord.ext import commands
import func
import server_config


class Waiter:
    def __init__(self, parent_cog, callback, embed_message, embed):
        self.parent = parent_cog
        self.callback = callback
        self.embed_message = embed_message
        self.embed = embed

    @staticmethod
    async def callback(message: discord.Message, zelf: "Waiter"):
        raise NotImplementedError("callback not implemented")


class WelcomeBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Join and Leave Announcements and Settings"
        self.emoji = "👋"
        self.pending_id = {}

    @commands.hybrid_group("welcome")
    async def welcome(self, ctx):
        """Welcome Bot Commands"""
        pass

    @welcome.command("setup")
    async def setup(self, ctx):
        """Setup the Welcome Bot"""
        await ctx.defer()
        welembed = (
            func.Embed()
            .color(0x11111B)
            .title("Welcome Listener Setup")
            .description("Welcome to the Welcome Listener Setup!")
        )
        emb = await ctx.send(embed=welembed.embed)
        await server_config.create_default_server_config(ctx.guild.id)
        welembed.description(
            "Please reply to this message with the channel ID of the welcome channel."
        )
        await emb.edit(embed=welembed.embed)

        async def callback(message: discord.Message, zelf: Waiter):
            try:
                channel = message.guild.get_channel(int(message.content))
            except (ValueError, discord.NotFound):
                print("invalid channel ID")
                zelf.embed.description("Please reply with a **valid** channel ID!")
                await zelf.embed_message.edit(embed=zelf.embed.embed)
                return
            print("valid channel ID")
            await server_config.set_server_welcome_channel(ctx.guild.id, channel.id)
            zelf.embed.description("Welcome Message Channel has been set!")
            await zelf.embed_message.edit(embed=zelf.embed.embed)
            print("removing waiter from the waiter list")
            zelf.parent.pending_id.pop(zelf.embed_message.id)

        print("adding waiter to the waiter list")
        self.pending_id[emb.id] = Waiter(self, callback, emb, welembed)

    @commands.Cog.listener("on_member_join")
    async def joinmsg(self, member):
        welid = await server_config.get_server_config(member.guild.id)
        await member.guild.get_channel_or_thread(welid["welcome_channel_id"]).send(
            func.Embed()
            .title(f"Welcome to {member.guild.name}!")
            .description(f"Welcome {member.mention}!")
            .thumbnail(member.avatar.url)
            .embed
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.reference is not None
            and message.reference.message_id in self.pending_id.keys()
        ):
            print("waiter found, passing event to callback")
            waiter = self.pending_id.get(message.reference.message_id)
            await waiter.callback(message, waiter)
        else:
            pass


async def setup(bot):
    await bot.add_cog(WelcomeBot(bot))
