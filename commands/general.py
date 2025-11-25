import logging
from discord.ext import commands
import discord
from config import Config

logger = logging.getLogger(__name__)

async def setup(bot):
    @bot.command()
    async def Hola(ctx):
        await ctx.send(f"Hola! Soy Pana, tu asistente personal. ¿En qué puedo ayudarte {ctx.author.mention}?")

    @bot.command()
    async def Say(ctx, *, texto: str):
        try:
            await ctx.message.delete()
            await ctx.send(texto)
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para eliminar mensajes.")
        except Exception as e:
            logger.error(f"Error in Say command: {e}", exc_info=True)
            await ctx.send(f"❌ Error: {str(e)}")

    @bot.command()
    async def Ping(ctx, user: discord.Member, cantidadPing: int, *args: str):
        if cantidadPing > Config.MAX_PING_COUNT:
            await ctx.send(f"⚠️ No puedes hacer más de {Config.MAX_PING_COUNT} pings.")
            return
        if cantidadPing < 1:
            await ctx.send("⚠️ Debes especificar al menos 1 ping.")
            return
        mensaje = " ".join(args) if args else ""
        try:
            for _ in range(cantidadPing):
                await ctx.send(f"{user.mention} {mensaje}")
        except Exception as e:
            logger.error(f"Error in Ping command: {e}", exc_info=True)
            await ctx.send(f"❌ Error: {str(e)}")

    @bot.command()
    async def Purge(ctx, cantidad: int):
        if cantidad < 1 or cantidad > Config.MAX_PURGE_COUNT:
            await ctx.send(f"⚠️ Debes especificar un número entre 1 y {Config.MAX_PURGE_COUNT}.")
            return
        try:
            deleted = await ctx.channel.purge(limit=cantidad + 1)
            await ctx.send(f"🗑️ Se eliminaron {len(deleted) - 1} mensajes", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para eliminar mensajes.")
        except Exception as e:
            logger.error(f"Error in Purge command: {e}", exc_info=True)
            await ctx.send(f"❌ Error: {str(e)}")

    @bot.command()
    async def Avatar(ctx, user: discord.Member = None):
        try:
            user = user or ctx.author
            embed = discord.Embed(title=f"Avatar de {user.name}", color=discord.Color.blue())
            if user.avatar:
                embed.set_image(url=user.avatar.url)
            else:
                embed.description = "Este usuario no tiene avatar personalizado."
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in Avatar command: {e}", exc_info=True)
            await ctx.send(f"❌ Error: {str(e)}")

    @bot.command()
    async def Help(ctx):
        embed = discord.Embed(
            title="📋 Comandos Disponibles",
            description="Lista de comandos del bot Pana",
            color=discord.Color.green()
        )
        embed.add_field(
            name="General",
            value="`panaHola` - Saludo del bot\n"
                  "`panaSay <texto>` - El bot repite el texto\n"
                  "`panaPing <usuario> <cantidad> [mensaje]` - Menciona a un usuario\n"
                  "`panaPurge <cantidad>` - Elimina mensajes\n"
                  "`panaAvatar [usuario]` - Muestra el avatar",
            inline=False
        )
        embed.add_field(
            name="IA",
            value="`panaIA <prompt>` - Pregunta a Gemini\n"
                  "`panaImageIA <prompt>` - Genera imagen con IA",
            inline=False
        )
        embed.add_field(
            name="Música",
            value="`panaPlay <canción>` - Reproduce música\n"
                  "`panaPause` - Pausa la música\n"
                  "`panaResume` - Reanuda la música\n"
                  "`panaStop` - Detiene la música\n"
                  "`panaPlayNext` - Salta a la siguiente canción\n"
                  "`panaJoin` - Une al bot al canal de voz\n"
                  "`panaLeave` - Desconecta el bot",
            inline=False
        )
        await ctx.send(embed=embed)