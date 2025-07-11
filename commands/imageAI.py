import discord
from discord.ext import commands
from huggingface_hub import InferenceClient
from PIL import Image
import os
import io

async def setup(bot):
    HF_TOKEN = os.getenv("HF_TOKEN") 
    client = InferenceClient(token=HF_TOKEN)

    @bot.command()
    async def ImageIA(ctx, *, prompt: str):
        await ctx.send(f"🎨 Generando imagen para: `{prompt}`... Esto puede tardar unos segundos.")

        try:
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
            await ctx.send(f"❌ Error generando imagen: {str(e)}")
