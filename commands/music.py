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

# Set FFmpeg path (supports local Windows, local bin folder in Render/Linux, or global PATH)
if os.path.exists("C:/ffmpeg/bin/ffmpeg.exe"):
    FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"
elif os.path.exists("./bin/ffmpeg"):
    FFMPEG_PATH = "./bin/ffmpeg"
else:
    FFMPEG_PATH = "ffmpeg"

# Handle cookies from Base64 environment variable (for Render deployment)
def get_cookies_file():
    """Get cookies file path, creating it from Base64 env var if needed"""
    cookies_base64 = os.getenv("YOUTUBE_COOKIES_BASE64")

    if cookies_base64:
        # Decode Base64 and write to temporary file
        try:
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')

            # Validate cookies content
            if not cookies_content.strip():
                logger.error("Decoded cookies file is empty")
                return None

            if '# Netscape HTTP Cookie File' not in cookies_content and '.youtube.com' not in cookies_content:
                logger.error("Cookies file doesn't appear to be valid YouTube cookies")
                logger.debug(f"Cookies preview: {cookies_content[:200]}")
                return None

            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
            temp_file.write(cookies_content)
            temp_file.close()
            logger.info(f"Created cookies file from Base64 env var at: {temp_file.name}")
            logger.info(f"Cookies file size: {len(cookies_content)} bytes")
            return temp_file.name
        except Exception as e:
            logger.error(f"Failed to decode Base64 cookies: {e}", exc_info=True)
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

        is_url = query.startswith("http://") or query.startswith("https://")

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'cachedir': False,
            'ignoreerrors': True,
        }

        # Use cookie file if it exists
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path

        def extract_audio():
            stream_url = None
            title = None

            # 1. Intentar con múltiples instancias públicas de Piped e Invidious (evita bloqueos de IP de Render)
            if not is_url:
                import urllib.request
                import json
                import urllib.parse
                encoded_q = urllib.parse.quote(query)
                
                piped_instances = [
                    "https://api.piped.private.coffee",
                    "https://pipedapi.kavin.rocks",
                    "https://pipedapi.adminforge.de",
                    "https://pipedapi.leptons.xyz",
                ]
                for instance in piped_instances:
                    try:
                        req = urllib.request.Request(f"{instance}/search?q={encoded_q}&filter=videos", headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            if resp.status == 200:
                                data = json.loads(resp.read().decode('utf-8'))
                                items = data.get('items', [])
                                for item in items[:2]:
                                    v_url = item.get('url', '')
                                    if 'v=' in v_url:
                                        video_id = v_url.split('v=')[-1]
                                        s_req = urllib.request.Request(f"{instance}/streams/{video_id}", headers={'User-Agent': 'Mozilla/5.0'})
                                        with urllib.request.urlopen(s_req, timeout=4) as s_resp:
                                            if s_resp.status == 200:
                                                s_data = json.loads(s_resp.read().decode('utf-8'))
                                                audio_streams = s_data.get('audioStreams', [])
                                                if audio_streams:
                                                    stream_url = audio_streams[0]['url']
                                                    title = s_data.get('title', item.get('title', 'Audio'))
                                                    logger.info(f"Obtenido stream vía Piped ({instance}): {title}")
                                                    return stream_url, title
                    except Exception as p_err:
                        logger.warning(f"Piped ({instance}) falló: {p_err}")

                invidious_instances = [
                    "https://inv.nadeko.net",
                    "https://invidious.nerdvpn.de",
                    "https://yewtu.be",
                ]
                for inv in invidious_instances:
                    try:
                        req = urllib.request.Request(f"{inv}/api/v1/search?q={encoded_q}&type=video", headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            if resp.status == 200:
                                results = json.loads(resp.read().decode('utf-8'))
                                if results and isinstance(results, list):
                                    video_id = results[0].get('videoId')
                                    if video_id:
                                        v_req = urllib.request.Request(f"{inv}/api/v1/videos/{video_id}", headers={'User-Agent': 'Mozilla/5.0'})
                                        with urllib.request.urlopen(v_req, timeout=4) as v_resp:
                                            if v_resp.status == 200:
                                                v_data = json.loads(v_resp.read().decode('utf-8'))
                                                audio_formats = [f for f in v_data.get('adaptiveFormats', []) if 'audio' in f.get('type', '')]
                                                if audio_formats:
                                                    stream_url = audio_formats[0]['url']
                                                    title = v_data.get('title', results[0].get('title', 'Audio'))
                                                    logger.info(f"Obtenido stream vía Invidious ({inv}): {title}")
                                                    return stream_url, title
                    except Exception as inv_err:
                        logger.warning(f"Invidious ({inv}) falló: {inv_err}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if is_url:
                    info = ydl.extract_info(query, download=False)
                    if info:
                        stream_url = info.get('url')
                        title = info.get('title', 'Audio')
                else:
                    # 2. Probar SoundCloud (generalmente no bloquea IPs de servidor)
                    try:
                        sc_results = ydl.extract_info(f"scsearch5:{query}", download=False)
                        entries = [e for e in sc_results.get('entries', []) if e and e.get('url')]
                        if entries:
                            stream_url = entries[0]['url']
                            title = entries[0].get('title', 'Audio')
                    except Exception as sc_err:
                        logger.warning(f"SoundCloud error: {sc_err}")

                    # 3. Si no se encontró en SoundCloud, probar YouTube
                    if not stream_url:
                        logger.info("Probando con ytsearch5...")
                        yt_results = ydl.extract_info(f"ytsearch5:{query}", download=False)
                        entries = [e for e in yt_results.get('entries', []) if e and e.get('url')]
                        if entries:
                            stream_url = entries[0]['url']
                            title = entries[0].get('title', 'Audio')
            return stream_url, title

        try:
            # Ejecutar yt-dlp en un hilo en segundo plano para no bloquear el heartbeat de Discord
            import asyncio
            stream_url, title = await asyncio.to_thread(extract_audio)

            if not stream_url:
                await ctx.send("❌ No se pudo encontrar una versión reproducible sin DRM. Prueba con otro término de búsqueda.")
                return

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
                        logger.error(f"Error during playback callback: {error}", exc_info=True)
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
