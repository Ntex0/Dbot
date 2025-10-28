import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
from mcrcon import MCRcon

#load .env file
load_dotenv()
rcon_password = os.getenv('rcon.password')
rcon_port = int(os.getenv('rcon.port'))

# get environmental variables
token = os.getenv('TOKEN')

handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Allow commands to be processed
    await bot.process_commands(message)

@bot.command(name="hello", description="Says hello")
async def hello(interaction):
    await interaction.response.send_message("Hello!")

@bot.tree.command(name="summon_zombie", description="Summons a zombie named Bob")
async def summon_zombie(interaction):
    await interaction.response.defer(thinking=True)
    
    try:
        with MCRcon("localhost", rcon_password, port=rcon_port) as mcr:
            response = mcr.command("summon zombie ~ ~1 ~ {CustomName:'&6CHIMMY CHANGA'}")
        await interaction.followup.send(f"{response}")
    except Exception as e:
        await interaction.followup.send(f"Error executing RCON command: {e}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
