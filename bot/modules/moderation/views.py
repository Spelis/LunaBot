import discord


class DismissibleByMentioned(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Dismiss",
        style=discord.ButtonStyle.danger,
        custom_id="dismissible_by_mentioned",
    )
    async def dismiss(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if button.custom_id != "dismissible_by_mentioned":
            return
        if not interaction.message:
            return
        if interaction.user.mentioned_in(interaction.message):
            await interaction.message.delete()
