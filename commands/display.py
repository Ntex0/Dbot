import discord
from discord.ext import commands
import requests
import json 
from discord import app_commands
import os
from main import ROOT


def PlayerUUID(player_name):
    uuid_api_url = f"https://api.mojang.com/users/profiles/minecraft/{player_name}" # accesses minecraft api to get uid to pass to other api for images
    response = requests.get(uuid_api_url)
    if response.status_code == 200:
        data_to_parse = response.json() # json file to be parsed for uuid
        player__uuid = data_to_parse.get("id")
        return player__uuid
    raise ValueError("Player not Found remember commands only work for premium minecraft accounts!")

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
            player_health = self.bot.mcr.command(f"data get entity {player_name} Health") # Gets our player health via rcon command
            player_hunger = self.bot.mcr.command(f"data get entity {player_name} foodLevel") # gets our player hunger via rcon command
            print(player_hunger)
            player_hunger = int(player_hunger.split(": ")[1].strip())
            player_health = float(player_health.split(": ")[1].strip().replace("f", ""))
            print(player_health)
            player_name = player_name.strip()
            parsed_uuid = PlayerUUID(player_name) # Helper function which grabs our players UUID
            if not parsed_uuid:
                await interaction.followup.send(f"Player data invalid for {player_name}", ephemeral=True)
                continue
            embed = discord.Embed(
                        title=f"{player_name}", # sets title of the embed to be player name
                        description=f"❤️: {player_health:.2f}/20.00\n🍖: {player_hunger:.2f}/20.00", # sets description of our embed
                        color=discord.Color.purple() # sets color of our embed
             )
            
            embed.set_image(url=f"https://mc-heads.net/avatar/{parsed_uuid}/50.png")
            print(f"https://crafatar.com/avatars/{parsed_uuid}")
            await interaction.followup.send(embed=embed, ephemeral=False) # Sends embed out to the channel
        
#cache_file =  os.path.join(ROOT, "cache", "player_cache.json")

#if not os.path.exists(cache_file):
    #with open(cache_file, "w") as f:
        #f.write("{}")
        #cache = json.load(f)

async def setup(bot):
    await bot.add_cog(Display(bot))