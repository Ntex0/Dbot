import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('TOKEN')

handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Allow commands to be processed
    await bot.process_commands(message)

@bot.command(name="hello", description="Says hello")
async def hello(interaction):
    await interaction.response.send_message("Hello!")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
