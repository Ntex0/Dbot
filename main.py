import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from mcrcon import MCRcon
import asyncio

#load .env file
load_dotenv()
rcon_password = os.getenv('rcon.password')
rcon_port = int(os.getenv('rcon.port'))
ip="localhost"

# get environmental variables
token = os.getenv('TOKEN')

handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
mcr = None
rcon_connected = False

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
    global ip
    ip = new_ip
    await interaction.response.send_message(f"IP address set to {ip}", ephemeral=True)

@bot.tree.command(name="getip", description="Gets the current IP address of the Minecraft server")
async def get_ip(interaction):
    await interaction.response.send_message(f"Current IP address is {ip}", ephemeral=True)
    

@bot.tree.command(name="connect", description="Connects to the Minecraft server via RCON")
async def connect(interaction):
    global mcr, rcon_connected
    
    if rcon_connected:
        await interaction.response.send_message("Already connected to RCON.", ephemeral=True)
        return
    async def try_connect():
        global mcr, rcon_connected
        mcr = MCRcon(ip, rcon_password, port=rcon_port)
        mcr.connect()

    try:
        await asyncio.wait_for(try_connect(), timeout=5)
        rcon_connected = True

        response = mcr.command("list")
        await interaction.response.send_message(f"Connected successfully at: {ip}:{rcon_port}\n{response}", ephemeral=True)

    except asyncio.TimeoutError:
        await interaction.response.send_message("Connection timed out. Please check the IP address and RCON settings.", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"Error connecting via RCON: {e}", ephemeral=True)

@bot.tree.command(name="disconnect", description="Disconnects from the Minecraft server RCON")
async def disconnect(interaction):
    global mcr, rcon_connected
    if not rcon_connected:
        await interaction.response.send_message("Not connected to server.", ephemeral=True)
        return

    try:
        mcr.disconnect()
        await interaction.response.send_message("Disconnected from Server successfully.", ephemeral=True)
        rcon_connected = False
    except Exception as e:
        await interaction.response.send_message(f"Error disconnecting from RCON: {e}", ephemeral=True)

@bot.tree.command(name="online", description="Lists all players currently online on the Minecraft server")
async def list_players(interaction: discord.Interaction):
    if rcon_connected is False:
        await interaction.response.send_message("Not connected to server.", ephemeral=True)
        return

    try:
        response = mcr.command("list")
        await interaction.response.send_message(f"Online Players:\n{response}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving player list: {e}", ephemeral=True)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
