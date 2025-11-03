import discord
from discord import app_commands
from discord.ext import commands
from menus.menus import open_menu
from menus.menus_old import Schema 


class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="give", description="Give a custom item to a player")
    async def give_command(self, interaction: discord.Interaction):
        schema = get_schema()
        selected_data = await open_menu(interaction, schema)
        # selected_data will contain a nested dict of the final selection
        print("User selection:", selected_data)

        # Here, construct your item/give command from selected_data
        # Example:
        # give_item(player, selected_data)
        await interaction.followup.send(f"Final selection: {selected_data}", ephemeral=True)

component_file = "../schema/components.json"
schema = Schema(component_file)





async def setup(bot):
    await bot.add_cog(Give(bot))
