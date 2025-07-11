import os
import sys
import subprocess
from discord.ext import commands

async def setup(bot):
    @bot.command()
    async def Open(ctx):
        app = r"C:/Program Files (x86)/GOG Galaxy/Games/Hollow Knight/Hollow Knight.exe"
        subprocess.Popen(app)

    @bot.command()
    async def ReloadBot(ctx):
        await ctx.send("♻️ Recargando bot...")
        os.execv(sys.executable, ['python'] + sys.argv)
