import discord
from discord.ext import commands
#import requests
from discord import app_commands

def PlayerUUID(player_name):
    pass

class Display(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server_members", description="Displays players on the server")
    async def display_online(self, interaction: discord.Interaction):
        list_players = self.bot.mcr.command("list")
        await interaction.response.send_message(list_players, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Display(bot))