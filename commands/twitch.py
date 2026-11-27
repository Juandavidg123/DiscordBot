import logging
import time
import aiohttp
import discord
from discord.ext import commands, tasks
from config import Config

logger = logging.getLogger(__name__)

class TwitchNotifier(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.access_token: str | None = None
        self.token_expires_at: float = 0
        self.is_live: bool = False
        self.last_stream_id: str | None = None
        self.user_cache: dict[str, dict] = {}

        # Iniciar la tarea periódica si las credenciales y canal están configurados
        if Config.TWITCH_CLIENT_ID and Config.TWITCH_CLIENT_SECRET and Config.TWITCH_CHANNEL_NAME:
            self.check_twitch_live.change_interval(seconds=max(30, Config.TWITCH_CHECK_INTERVAL))
            self.check_twitch_live.start()
            logger.info("📡 Tarea de verificación periódica de Twitch iniciada.")
        else:
            logger.warning("⚠️ TwitchNotifier cargado, pero faltan variables de configuración (TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET o TWITCH_CHANNEL_NAME).")

    def cog_unload(self):
        if self.check_twitch_live.is_running():
            self.check_twitch_live.cancel()
        if self.session and not self.session.closed:
            self.bot.loop.create_task(self.session.close())

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_access_token(self) -> str | None:
        """Obtiene o reutiliza el token de acceso de Twitch Helix API."""
        if not Config.TWITCH_CLIENT_ID or not Config.TWITCH_CLIENT_SECRET:
            return None

        # Reutilizar si aún es válido
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        session = await self.get_session()
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": Config.TWITCH_CLIENT_ID,
            "client_secret": Config.TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }

        try:
            async with session.post(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self.token_expires_at = time.time() + expires_in - 60
                    logger.info("🔑 Nuevo token de acceso de Twitch obtenido exitosamente.")
                    return self.access_token
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Error al obtener token de Twitch: HTTP {resp.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ Excepción conectando a Twitch OAuth: {e}", exc_info=True)
            return None

    async def get_user_info(self, login_name: str) -> dict | None:
        """Obtiene información pública del usuario (como avatar y nombre para mostrar)."""
        clean_name = login_name.lower().strip()
        if clean_name in self.user_cache:
            return self.user_cache[clean_name]

        token = await self.get_access_token()
        if not token:
            return None

        session = await self.get_session()
        url = f"https://api.twitch.tv/helix/users?login={clean_name}"
        headers = {
            "Client-ID": Config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}"
        }

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    users = data.get("data", [])
                    if users:
                        user_info = users[0]
                        self.user_cache[clean_name] = user_info
                        return user_info
        except Exception as e:
            logger.error(f"Error consultando usuario Twitch: {e}")
        return None

    async def get_stream_data(self, channel_name: str = None) -> dict | None:
        """Consulta si un canal de Twitch está en directo y devuelve su información."""
        channel = (channel_name or Config.TWITCH_CHANNEL_NAME or "").lower().strip()
        if not channel:
            return None

        token = await self.get_access_token()
        if not token:
            return None

        session = await self.get_session()
        url = f"https://api.twitch.tv/helix/streams?user_login={channel}"
        headers = {
            "Client-ID": Config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}"
        }

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    streams = data.get("data", [])
                    return streams[0] if streams else None
                elif resp.status == 401:
                    # Token posiblemente vencido, invalidar para la próxima
                    self.access_token = None
                    logger.warning("Token de Twitch rechazado (401), invalidado para renovación.")
                    return None
                else:
                    text = await resp.text()
                    logger.error(f"Error en API de Twitch streams: {resp.status} - {text}")
                    return None
        except Exception as e:
            logger.error(f"Excepción al consultar stream en Twitch: {e}", exc_info=True)
            return None

    def build_stream_embed(self, stream: dict, user_info: dict | None = None) -> discord.Embed:
        """Genera un embed con formato profesional para la alerta de stream."""
        user_name = stream.get("user_name") or stream.get("user_login", "Streamer")
        user_login = stream.get("user_login", user_name).lower()
        title = stream.get("title") or "¡En directo ahora!"
        game_name = stream.get("game_name") or "Sin categoría"
        viewer_count = stream.get("viewer_count", 0)
        stream_url = f"https://twitch.tv/{user_login}"

        embed = discord.Embed(
            title=f"🔴 {user_name} está en directo en Twitch",
            url=stream_url,
            description=f"**{title}**\n\n👉 [¡Entra al directo aquí!]({stream_url})",
            color=0x9146FF  # Púrpura Twitch
        )

        embed.add_field(name="🎮 Jugando / Categoría", value=game_name, inline=True)
        embed.add_field(name="👥 Espectadores", value=f"{viewer_count:,}", inline=True)

        # Miniatura del stream (con timestamp para evitar caché antiguo)
        raw_thumb = stream.get("thumbnail_url", "")
        if raw_thumb:
            thumb_url = raw_thumb.replace("{width}", "1280").replace("{height}", "720")
            thumb_url = f"{thumb_url}?t={int(time.time())}"
            embed.set_image(url=thumb_url)

        # Foto de perfil del streamer en autor y thumbnail
        if user_info and user_info.get("profile_image_url"):
            avatar_url = user_info["profile_image_url"]
            embed.set_author(name=user_name, url=stream_url, icon_url=avatar_url)
            embed.set_thumbnail(url=avatar_url)
        else:
            embed.set_author(name=user_name, url=stream_url)

        embed.set_footer(text="Twitch Live Alert", icon_url="https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png")
        embed.timestamp = discord.utils.utcnow()
        return embed

    def get_mention_content(self, user_name: str, stream_url: str) -> str:
        """Formatea la mención para la notificación."""
        mention = (Config.TWITCH_MENTION or "").strip()
        if mention.lower() == "everyone":
            prefix = "@everyone"
        elif mention.lower() == "here":
            prefix = "@here"
        elif mention.isdigit():
            prefix = f"<@&{mention}>"
        elif mention:
            prefix = mention
        else:
            prefix = ""

        if prefix:
            return f"🚨 {prefix} ¡**{user_name}** prendió directo en Twitch! Vénganse pa acá:\n{stream_url}"
        return f"🚨 ¡**{user_name}** prendió directo en Twitch! Vénganse pa acá:\n{stream_url}"

    async def send_live_notification(self, stream: dict):
        """Envía la alerta al canal de Discord configurado."""
        if not Config.TWITCH_DISCORD_CHANNEL_ID:
            logger.warning("No se ha configurado TWITCH_DISCORD_CHANNEL_ID; no se pudo enviar el aviso.")
            return

        channel = self.bot.get_channel(Config.TWITCH_DISCORD_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(Config.TWITCH_DISCORD_CHANNEL_ID)
            except Exception as e:
                logger.error(f"No se pudo encontrar el canal {Config.TWITCH_DISCORD_CHANNEL_ID}: {e}")
                return

        user_login = stream.get("user_login", "")
        user_info = await self.get_user_info(user_login) if user_login else None
        embed = self.build_stream_embed(stream, user_info)
        stream_url = f"https://twitch.tv/{user_login}"
        user_name = stream.get("user_name", user_login)
        content = self.get_mention_content(user_name, stream_url)

        try:
            await channel.send(content=content, embed=embed)
            logger.info(f"📢 Notificación de directo enviada a #{channel.name} para {user_name} (Stream ID: {stream.get('id')})")
        except discord.Forbidden:
            logger.error(f"⛔ Permiso denegado al enviar mensaje en canal {channel.id}")
        except Exception as e:
            logger.error(f"Error al enviar mensaje de stream en Discord: {e}", exc_info=True)

    @tasks.loop(seconds=60)
    async def check_twitch_live(self):
        """Bucle en segundo plano que consulta si el canal configurado está en vivo."""
        if not Config.TWITCH_CLIENT_ID or not Config.TWITCH_CLIENT_SECRET or not Config.TWITCH_CHANNEL_NAME:
            return

        try:
            stream = await self.get_stream_data(Config.TWITCH_CHANNEL_NAME)
            if stream:
                stream_id = stream.get("id")
                # Si acaba de iniciar o cambió de sesión/stream ID
                if not self.is_live or (stream_id and stream_id != self.last_stream_id):
                    self.is_live = True
                    self.last_stream_id = stream_id
                    await self.send_live_notification(stream)
            else:
                # El stream está apagado
                if self.is_live:
                    logger.info(f"Directo de {Config.TWITCH_CHANNEL_NAME} finalizado.")
                self.is_live = False
                self.last_stream_id = None
        except Exception as e:
            logger.error(f"Error en tarea check_twitch_live: {e}", exc_info=True)

    @check_twitch_live.before_loop
    async def before_check_twitch_live(self):
        await self.bot.wait_until_ready()

    @commands.command(name="Twitch", aliases=["twitch", "stream", "directo"])
    async def twitch_command(self, ctx: commands.Context, channel_name: str = None):
        """Muestra el estado actual de un canal de Twitch o del canal configurado."""
        target_channel = channel_name or Config.TWITCH_CHANNEL_NAME

        if not target_channel:
            await ctx.send("❌ No hay un canal configurado por defecto. Usa `panaTwitch <nombre_canal>`.")
            return

        if not Config.TWITCH_CLIENT_ID or not Config.TWITCH_CLIENT_SECRET:
            await ctx.send("⚠️ Faltan credenciales de Twitch (`TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET`).")
            return

        async with ctx.typing():
            stream = await self.get_stream_data(target_channel)
            user_info = await self.get_user_info(target_channel)

            if stream:
                embed = self.build_stream_embed(stream, user_info)
                await ctx.send(embed=embed)
            else:
                display_name = user_info.get("display_name", target_channel) if user_info else target_channel
                embed = discord.Embed(
                    title=f"⚪ {display_name} está desconectado",
                    description=f"El canal **{display_name}** no está transmitiendo en este momento.\n\nPuedes visitarlo en: https://twitch.tv/{target_channel.lower()}",
                    color=discord.Color.dark_grey()
                )
                if user_info and user_info.get("profile_image_url"):
                    embed.set_thumbnail(url=user_info["profile_image_url"])
                embed.set_footer(text="Twitch Status", icon_url="https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png")
                await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchNotifier(bot))
