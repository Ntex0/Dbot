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

@bot.command(name="setip", help="Sets the IP address of the Minecraft server")
async def set_ip(ctx, new_ip: str):
    global ip
    ip = new_ip
    await ctx.send(f"IP address set to {ip}")

@bot.command(name="getip", help="Gets the current IP address of the Minecraft server")
async def get_ip(ctx):
    await ctx.send(f"Current IP address is {ip}")

@bot.tree.command(name="connect", description="Connects to the Minecraft server via RCON")
async def connect(interaction):
    global mcr, rcon_connected
    await interaction.response.defer(thinking=True)
    
    if rcon_connected:
        await interaction.followup.send("Already connected to RCON.", ephemeral=True)
        return

    async def try_connect():
        global mcr, rcon_connected
        mcr = MCRcon(ip, rcon_password, port=rcon_port)
        mcr.connect()

    try:
        await asyncio.wait_for(try_connect(), timeout=5)
        rcon_connected = True

        response = mcr.command("list")
        await interaction.followup.send(f"Connected successfully at: {ip}:{rcon_port}\n{response}")

    except asyncio.TimeoutError:
        await interaction.followup.send("Connection timed out. Please check the IP address and RCON settings.")

    except Exception as e:
        await interaction.followup.send(f"Error connecting via RCON: {e}", ephemeral=True)

@bot.tree.command(name="disconect", description="Disconnects from the Minecraft server RCON")
async def disconnect(interaction):
    await interaction.response.defer(thinking=True)
    if rcon_connected is False:
        await interaction.followup.send("Not connected to server.", ephemeral=True)
        return

    try:
        mcr.disconnect()
        await interaction.followup.send("Disconnected from Server successfully.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error disconnecting from RCON: {e}", ephemeral=True)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
