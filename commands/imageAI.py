import logging
import discord
from discord.ext import commands
import aiohttp
import urllib.parse
import io

logger = logging.getLogger(__name__)

async def setup(bot):
    @bot.command(name="Image", aliases=["ImageIA", "image"])
    async def image_cmd(ctx, *, prompt: str):
        try:
            await ctx.send(f"🎨 Generando imagen para: `{prompt}`... Esto puede tardar unos segundos.")

            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        buffer = io.BytesIO(image_bytes)
                        buffer.seek(0)
                        await ctx.send(file=discord.File(buffer, filename="generated.png"))
                    else:
                        await ctx.send(f"❌ Error al generar la imagen (código {response.status}).")

        except Exception as e:
            logger.error(f"Error in Image command: {e}", exc_info=True)
            await ctx.send(f"❌ Error generando imagen: {str(e)}")
