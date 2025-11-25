import os
import logging
import discord
from discord.ext import commands
import asyncio
import webserver
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=Config.COMMAND_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot conectado como {bot.user}")
    logger.info(f"Total de comandos registrados: {len(bot.commands)}")
    for cmd in bot.commands:
        logger.info(f"  - {cmd.name}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado. Usa `panaHelp` para ver comandos disponibles.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un argumento: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argumento inválido: {str(error)}")
    else:
        logger.error(f"Error en comando: {error}", exc_info=True)
        await ctx.send(f"❌ Ocurrió un error: {str(error)}")

async def main():
    extensions_loaded = set()
    for filename in os.listdir('./commands'):
        if filename.endswith('.py') and filename != '__init__.py':
            extension_name = f'commands.{filename[:-3]}'
            if extension_name not in extensions_loaded:
                try:
                    await bot.load_extension(extension_name)
                    extensions_loaded.add(extension_name)
                    logger.info(f"✅ Comando cargado: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error al cargar {filename}: {e}", exc_info=True)

    await bot.start(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    webserver.keep_alive()
    asyncio.run(main())
