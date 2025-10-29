import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from mcrcon import MCRcon

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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


@bot.tree.command(name="connect", description="Connects to the Minecraft server via RCON")
async def connect(interaction):
    global mcr
    await interaction.response.defer(thinking=True)
    if mcr is not None:
        await interaction.followup.send("Already connected to RCON.", ephemeral=True)
        return
    try:
        mcr = MCRcon(ip, rcon_password, port=rcon_port)
        mcr.connect()
        response = mcr.command("list")
        await interaction.followup.send(f"Connected Successfully: {response}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error connecting via RCON: {e}", ephemeral=True)

@bot.tree.command(name="disconect", description="Disconnects from the Minecraft server RCON")
async def disconnect(interaction):
    await interaction.response.defer(thinking=True)
    if mcr is None:
        await interaction.followup.send("Not connected to server.", ephemeral=True)
        return
    try:
        mcr.disconnect()
        await interaction.followup.send("Disconnected from Server successfully.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error disconnecting from RCON: {e}", ephemeral=True)

@bot.tree.command(name="summon_zombie", description="Summons a zombie named Bob")
async def summon_zombie(interaction):
    await interaction.response.defer(thinking=True)
    
    try:
        response = mcr.command(
                "summon zombie 273 119 -327 {CustomName:'§6CHIMMY CHANGA', Health:40.0f,Attributes:[{Name:'generic.maxHealth',Base:40.0}]}")
        await interaction.followup.send(f"{response}")
    except Exception as e:
        await interaction.followup.send(f"Error executing RCON command: {e}")

@bot.tree.command(name="give_super_boots", description="Give super step boots")
async def give(interaction):
    await interaction.response.defer(thinking=True)
    
    try:
        response = mcr.command("give @p minecraft:diamond_boots[attribute_modifiers=[{type:'step_height', amount:10.0, operation:'add_value', id:'example:custom_step_height', slot:'feet'}], enchantments={unbreaking:3}]")
        await interaction.followup.send(f"{response}")
    except Exception as e:
        await interaction.followup.send(f"Error executing RCON command: {e}")
bot.run(token, log_handler=handler, log_level=logging.DEBUG)
