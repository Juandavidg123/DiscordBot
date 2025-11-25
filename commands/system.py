import os
import sys
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

async def setup(bot):
    @bot.command()
    @commands.is_owner()
    async def ReloadBot(ctx):
        try:
            await ctx.send("♻️ Recargando bot...")
            logger.info("Bot reload requested by owner")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            logger.error(f"Error reloading bot: {e}", exc_info=True)
            await ctx.send(f"❌ Error al recargar: {str(e)}")
