import discord
from discord.ext import commands
import requests
from discord import app_commands

def PlayerUUID(player_name):
    uuid_api_url = f"https://api.mojang.com/users/profiles/minecraft/{player_name}" # accesses minecraft api to get uid to pass to other api for images
    response = requests.get(uuid_api_url)
    if response.status_code == 200:
        data_to_parse = response.json() # json file to be parsed for uuid
        player__uuid = data_to_parse.get("id")
        print(player__uuid)

class Display(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server_members", description="Displays players on the server")
    async def display_online(self, interaction: discord.Interaction):
        list_of_players = self.bot.mcr.command("list")
        parsed_list_players = list_of_players.split(": ")[1].strip()
        parsed_list_players = parsed_list_players.split(", ")
        await interaction.response.send_message(list_of_players, ephemeral=True)
        for player_name in parsed_list_players:
            player_name = player_name.strip()
            PlayerUUID(player_name)
            await interaction.followup.send(f"Player is {player_name}")

async def setup(bot):
    await bot.add_cog(Display(bot))