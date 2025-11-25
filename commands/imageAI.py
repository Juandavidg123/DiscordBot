import logging
import discord
from discord.ext import commands
from huggingface_hub import InferenceClient
from PIL import Image
import io
from config import Config

logger = logging.getLogger(__name__)

async def setup(bot):
    if not Config.HF_TOKEN:
        logger.warning("HF_TOKEN not configured, ImageIA command will not work")
        return

    client = InferenceClient(token=Config.HF_TOKEN)

    @bot.command()
    async def ImageIA(ctx, *, prompt: str):
        try:
            await ctx.send(f"🎨 Generando imagen para: `{prompt}`... Esto puede tardar unos segundos.")

            image: Image.Image = client.text_to_image(
                prompt,
                model="stabilityai/stable-diffusion-xl-base-1.0",
                guidance_scale=7.5,
                num_inference_steps=50
            )

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            await ctx.send(file=discord.File(buffer, filename="generated.png"))

        except Exception as e:
            logger.error(f"Error in ImageIA command: {e}", exc_info=True)
            await ctx.send(f"❌ Error generando imagen: {str(e)}")
