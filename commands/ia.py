import logging
from discord.ext import commands
from api.gemini import data
from utils.utils import dividir_texto

logger = logging.getLogger(__name__)

async def setup(bot):
    @bot.command()
    async def IA(ctx, *, prompt: str):
        try:
            async with ctx.typing():
                respuesta = await data(prompt)

            if respuesta.startswith("Error:"):
                await ctx.send(f"❌ {respuesta}")
                return

            partes = dividir_texto(respuesta)
            for parte in partes:
                await ctx.send(parte)
        except Exception as e:
            logger.error(f"Error in IA command: {e}", exc_info=True)
            await ctx.send(f"❌ Error al procesar tu solicitud: {str(e)}")