import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from mcrcon import MCRcon
import asyncio

# load .env file
load_dotenv()

RCON_PASSWORD = os.getenv('rcon.password')
RCON_PORT = int(str(os.getenv('rcon.port')))

# set project root path
ROOT = os.path.dirname(os.path.abspath(__file__))

# get environmental variables
token = os.getenv('TOKEN')
if token is None:
    raise ValueError("Token not found")

handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Dbot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcr = None
        self.rcon_connected = False
        self.ip = "localhost"

bot = Dbot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


@bot.tree.command(name="setip", description="Sets the IP address of the Minecraft server")
async def set_ip(interaction, new_ip: str):
    bot.ip = new_ip
    await interaction.response.send_message(f"IP address set to {bot.ip}", ephemeral=True)

    await asyncio.sleep(3)
    await interaction.delete_original_response()

@bot.tree.command(name="getip", description="Gets the current IP address of the Minecraft server")
async def get_ip(interaction):
    await interaction.response.send_message(f"Current IP address is {bot.ip}", ephemeral=True)
    
    await asyncio.sleep(3)
    await interaction.delete_original_response()

@bot.tree.command(name="connect", description="Connects to the Minecraft server via RCON")
async def connect(interaction):
    if bot.rcon_connected:
        await interaction.response.send_message("Already connected to RCON.", ephemeral=True)
        return

    async def try_connect(bot):
        bot.mcr = MCRcon(bot.ip, RCON_PASSWORD, port=RCON_PORT)
        bot.mcr.connect()

    try:
        await asyncio.wait_for(try_connect(bot), timeout=5)
        bot.rcon_connected = True

        response = bot.mcr.command("list") # type: ignore
        await interaction.response.send_message(f"Connected successfully at: {bot.ip}:{RCON_PORT}\n{response}", ephemeral=True)

    except asyncio.TimeoutError:
        await interaction.response.send_message("Connection timed out. Please check the IP address and RCON settings.", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"Error connecting via RCON: {e}", ephemeral=True)
    
    await asyncio.sleep(3)
    await interaction.delete_original_response()


@bot.tree.command(name="disconnect", description="Disconnects from the Minecraft server RCON")
async def disconnect(interaction):
    if not bot.rcon_connected:
        await interaction.response.send_message("Not connected to server.", ephemeral=True)
        return

    try:
        bot.mcr.disconnect() # type: ignore
        await interaction.response.send_message("Disconnected from Server successfully.", ephemeral=True)
        bot.rcon_connected = False
    except Exception as e:
        await interaction.response.send_message(f"Error disconnecting from RCON: {e}", ephemeral=True)

    await asyncio.sleep(3)
    await interaction.delete_original_response()

@bot.tree.command(name="online", description="Lists all players currently online on the Minecraft server")
async def list_players(interaction: discord.Interaction):
    if bot.rcon_connected is False:
        await interaction.response.send_message("Not connected to server.", ephemeral=True)
        return

    try:
        response = bot.mcr.command("list")  # type: ignore
        await interaction.response.send_message(f"Online Players:\n{response}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving player list: {e}", ephemeral=True)

    await asyncio.sleep(3)
    await interaction.delete_original_response()

if __name__ == "__main__":
    # Load command cogs
    async def load_cogs():
        await bot.load_extension("commands.give")

    asyncio.run(load_cogs())

    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
