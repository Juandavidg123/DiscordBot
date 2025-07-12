import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import webserver

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="pana", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

async def main():
    for filename in os.listdir('./commands'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(f"✅ Comando cargado: {filename}")
            except Exception as e:
                print(f"❌ Error al cargar {filename}: {e}")

    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    webserver.keep_alive()
    asyncio.run(main())
