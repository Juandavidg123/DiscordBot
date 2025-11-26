import os
import logging
import base64
import tempfile
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer
import yt_dlp
from config import Config

logger = logging.getLogger(__name__)
queueSongs = []

# Explicitly set FFmpeg path (for local development)
FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe" if os.path.exists("C:/ffmpeg/bin/ffmpeg.exe") else "ffmpeg"

# Handle cookies from Base64 environment variable (for Render deployment)
def get_cookies_file():
    """Get cookies file path, creating it from Base64 env var if needed"""
    cookies_base64 = os.getenv("YOUTUBE_COOKIES_BASE64")

    if cookies_base64:
        # Decode Base64 and write to temporary file
        try:
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            temp_file.write(cookies_content)
            temp_file.close()
            logger.info(f"Created cookies file from Base64 env var at: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            logger.error(f"Failed to decode Base64 cookies: {e}")
            return None

    # Fallback to local file
    cookies_path = Config.COOKIES_FILE
    if os.path.exists(cookies_path):
        logger.info(f"Using local cookies file: {cookies_path}")
        return cookies_path

    logger.warning("No cookies file found")
    return None

async def setup(bot):
    @bot.command()
    async def Play(ctx, *, query: str):
        # Get cookies file (from Base64 env var or local file)
        cookies_path = get_cookies_file()

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'quiet': True,
            'default_search': 'ytsearch',
            'noplaylist': False,
            'extract_flat': False,
            'no_warnings': True,
            'ignoreerrors': False,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'ios'],
                    'player_skip': ['configs'],
                    'skip': ['hls', 'dash']
                }
            },
            'age_limit': None,
            'nocheckcertificate': True,
        }

        # Use cookie file if it exists (required for server deployment)
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:  # si fue búsqueda
                    info = info['entries'][0]

            stream_url = info['url']
            title = info.get('title', 'Audio')

            # Verifica si el usuario está en canal de voz
            if ctx.author.voice is None:
                await ctx.send("❌ Debes estar en un canal de voz.")
                return

            # Conexión al canal de voz
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()

            voice = ctx.voice_client

            if voice.is_playing():
                queueSongs.append((stream_url, title))
                await ctx.send(f"🎶 Agregado a la cola: {title}")
            else:
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn -ar 48000 -ac 2 -b:a 128k'
                }

                def after_playing(error):
                    if error:
                        logger.error(f"Error during playback: {error}")
                    else:
                        logger.info("Playback finished successfully")
                    bot.loop.create_task(play_next(ctx, bot))

                try:
                    logger.info(f"Attempting to play: {title}")

                    # Create audio source with explicit FFmpeg path
                    source = FFmpegPCMAudio(stream_url, executable=FFMPEG_PATH, **ffmpeg_options)
                    # Set volume to 100%
                    source = PCMVolumeTransformer(source, volume=1.0)

                    voice.play(source, after=after_playing)
                    logger.info(f"Successfully started playing: {title}")
                    await ctx.send(f"▶️ Reproduciendo: {title}")
                except Exception as play_error:
                    logger.error(f"Error starting playback: {play_error}", exc_info=True)
                    await ctx.send(f"❌ Error al reproducir: {str(play_error)}")

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                logger.error(f"YouTube bot detection triggered: {e}")
                await ctx.send("❌ YouTube requiere autenticación. Las cookies han expirado.\n"
                             "💡 El administrador debe actualizar las cookies de YouTube.\n"
                             "Instrucciones: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies")
            elif 'Video unavailable' in error_msg:
                await ctx.send("❌ El video no está disponible o es privado.")
            else:
                logger.error(f"Download error: {e}")
                await ctx.send(f"❌ Error al obtener el audio. Intenta con otro video.")
        except Exception as e:
            logger.error(f"Error playing music: {e}", exc_info=True)
            await ctx.send(f"❌ Error inesperado: {str(e)}")

    async def play_next(ctx, bot):
        if queueSongs:
            stream_url, title = queueSongs.pop(0)
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn -ar 48000 -ac 2 -b:a 128k'
            }

            def after_playing(error):
                if error:
                    logger.error(f"Error during playback: {error}")
                bot.loop.create_task(play_next(ctx, bot))

            source = FFmpegPCMAudio(stream_url, executable=FFMPEG_PATH, **ffmpeg_options)
            source = PCMVolumeTransformer(source, volume=1.0)
            ctx.voice_client.play(source, after=after_playing)
            await ctx.send(f"▶️ Reproduciendo: {title}")
        else:
            await ctx.send("🛑 No hay más canciones en la cola.")

    @bot.command()
    async def Pause(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Reproducción pausada.")

    @bot.command()
    async def Resume(ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Reproducción reanudada.")

    @bot.command()
    async def Stop(ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            queueSongs.clear()
            await ctx.send("⏹️ Reproducción detenida.")

    @bot.command()
    async def PlayNext(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Saltando a la siguiente canción...")
        elif queueSongs:
            await play_next(ctx, bot)
        else:
            await ctx.send("⚠️ No hay canciones para reproducir.")

    @bot.command()
    async def Join(ctx):
        if ctx.author.voice is None:
            await ctx.send("❌ No estás en un canal de voz.")
            return
        await ctx.author.voice.channel.connect()

    @bot.command()
    async def Leave(ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

    @bot.command()
    async def Volume(ctx, volume: int):
        """Ajusta el volumen (0-100)"""
        if not ctx.voice_client:
            await ctx.send("❌ No estoy en un canal de voz.")
            return

        if not 0 <= volume <= 100:
            await ctx.send("❌ El volumen debe estar entre 0 y 100.")
            return

        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"🔊 Volumen ajustado a {volume}%")
        else:
            await ctx.send("❌ No hay nada reproduciéndose.")
