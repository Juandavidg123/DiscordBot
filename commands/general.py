from discord.ext import commands
import discord

async def setup(bot):
    @bot.command()
    async def Hola(ctx):
        await ctx.send(f"Hola! Soy Pana, tu asistente personal. ¿En qué puedo ayudarte {ctx.author.mention}?")

    @bot.command()
    async def Say(ctx, *, texto: str):
        await ctx.message.delete()
        await ctx.send(texto)

    @bot.command()
    async def Ping(ctx, user: discord.Member, cantidadPing: int, *args: str):
        if cantidadPing > 10:
            await ctx.send("⚠️ No puedes hacer más de 10 pings.")
            return
        mensaje = " ".join(args)
        for _ in range(cantidadPing):
            await ctx.send(f"{user.mention} {mensaje}")

    @bot.command()
    async def Purge(ctx, cantidad: int):
        if cantidad < 1 or cantidad > 100:
            await ctx.send("⚠️ Debes especificar un número entre 1 y 100.")
            return
        deleted = await ctx.channel.purge(limit=cantidad + 1)
        await ctx.send(f"🗑️ Se eliminaron {len(deleted) - 1} mensajes")
    
    @bot.command()
    async def Avatar(ctx, user: discord.Member = None):
        user = user or ctx.author
        embed = discord.Embed(title=f"Avatar de {user.name}", color=discord.Color.blue())
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)