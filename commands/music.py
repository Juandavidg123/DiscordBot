import os
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer
import yt_dlp

queueSongs = []

async def setup(bot):
    @bot.command()
    async def Play(ctx, *, query: str):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'default_search': 'ytsearch',
            'noplaylist': False,
            'cookiefile': 'etc/secrets/cookiesYT.txt', # Ruta productivo al archivo de cookies
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
            }
        }

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
                source = PCMVolumeTransformer(FFmpegPCMAudio(stream_url))
                voice.play(source, after=lambda e: bot.loop.create_task(play_next(ctx, bot)))
                await ctx.send(f"▶️ Reproduciendo: {title}")

        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    async def play_next(ctx, bot):
        if queueSongs:
            stream_url, title = queueSongs.pop(0)
            source = PCMVolumeTransformer(FFmpegPCMAudio(stream_url))
            ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx, bot)))
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