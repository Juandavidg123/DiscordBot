# commands/ia.py
from discord.ext import commands
from api.gemini import data
from utils.utils import dividir_texto

async def setup(bot):
    @bot.command()
    async def IA(ctx, *, prompt: str):
        respuesta = await data(prompt)
        partes = dividir_texto(respuesta)
        for parte in partes:
            await ctx.send(parte)