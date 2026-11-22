import logging
import discord
from discord.ext import commands
import wavelink

logger = logging.getLogger(__name__)

async def setup(bot):
    @bot.command(name="Play", aliases=["play", "p"])
    async def Play(ctx, *, query: str):
        """Reproduce una canción o playlist vía Lavalink."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Debes estar conectado a un canal de voz.")
            return

        # Obtener o conectar el player de Wavelink
        player: wavelink.Player = ctx.voice_client

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            except Exception as e:
                logger.error(f"Error conectando a voz: {e}", exc_info=True)
                await ctx.send(f"❌ Error al conectar al canal de voz: {str(e)}")
                return
        elif player.channel.id != ctx.author.voice.channel.id:
            await player.move_to(ctx.author.voice.channel)

        await ctx.send(f"🔍 Buscando: `{query}`...")

        try:
            # Buscar pistas (YouTube Music por defecto, o URL directa)
            tracks: wavelink.Search = await wavelink.Playable.search(query)
            if not tracks:
                # Intento alternativo en YouTube o SoundCloud
                tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTube)

            if not tracks:
                await ctx.send("❌ No se encontraron resultados para tu búsqueda.")
                return

            if isinstance(tracks, wavelink.Playlist):
                added: int = await player.queue.put_wait(tracks)
                await ctx.send(f"🎶 Playlist añadida: **{tracks.name}** ({added} canciones)")
            else:
                track: wavelink.Playable = tracks[0]
                await player.queue.put_wait(track)
                await ctx.send(f"🎶 Añadida a la cola: **{track.title}** ({track.author})")

            # Si el player no está reproduciendo nada, comenzar
            if not player.playing:
                next_track = await player.queue.get_wait()
                await player.play(next_track)
                await ctx.send(f"▶️ Reproduciendo ahora: **{next_track.title}**")

        except Exception as e:
            logger.error(f"Error al reproducir pista en Wavelink: {e}", exc_info=True)
            await ctx.send(f"❌ Error en la reproducción: {str(e)}")

    @bot.command(name="Pause", aliases=["pause"])
    async def Pause(ctx):
        """Pausa la reproducción actual."""
        player: wavelink.Player = ctx.voice_client
        if not player or not player.playing:
            await ctx.send("❌ No hay nada reproduciéndose.")
            return

        if player.paused:
            await ctx.send("⚠️ La música ya está pausada.")
            return

        await player.pause(True)
        await ctx.send("⏸️ Reproducción pausada.")

    @bot.command(name="Resume", aliases=["resume"])
    async def Resume(ctx):
        """Reanuda la música pausada."""
        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.send("❌ No estoy conectado a ningún canal de voz.")
            return

        if not player.paused:
            await ctx.send("⚠️ La música no está pausada.")
            return

        await player.pause(False)
        await ctx.send("▶️ Reproducción reanudada.")

    @bot.command(name="Stop", aliases=["stop"])
    async def Stop(ctx):
        """Detiene la música y limpia la cola."""
        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.send("❌ No estoy conectado a ningún canal de voz.")
            return

        player.queue.clear()
        await player.stop()
        await ctx.send("⏹️ Reproducción detenida y cola vaciada.")

    @bot.command(name="PlayNext", aliases=["skip", "next"])
    async def PlayNext(ctx):
        """Salta a la siguiente canción en la cola."""
        player: wavelink.Player = ctx.voice_client
        if not player or not player.playing:
            await ctx.send("❌ No hay ninguna canción reproduciéndose.")
            return

        await player.skip(force=True)
        await ctx.send("⏭️ Canción saltada.")

    @bot.command(name="Join", aliases=["join"])
    async def Join(ctx):
        """Conecta al bot a tu canal de voz."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Debes estar conectado a un canal de voz.")
            return

        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.author.voice.channel.connect(cls=wavelink.Player)
            await ctx.send("✅ Conectado al canal de voz.")
        else:
            await player.move_to(ctx.author.voice.channel)
            await ctx.send("✅ Movido al canal de voz.")

    @bot.command(name="Leave", aliases=["leave", "disconnect"])
    async def Leave(ctx):
        """Desconecta al bot del canal de voz."""
        player: wavelink.Player = ctx.voice_client
        if player:
            await player.disconnect()
            await ctx.send("👋 Desconectado del canal de voz.")
        else:
            await ctx.send("❌ No estoy en ningún canal de voz.")

    @bot.command(name="Volume", aliases=["volume", "vol"])
    async def Volume(ctx, volume: int):
        """Ajusta el volumen (0 a 100)."""
        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.send("❌ No estoy conectado a un canal de voz.")
            return

        if not 0 <= volume <= 100:
            await ctx.send("❌ El volumen debe estar entre 0 y 100.")
            return

        await player.set_volume(volume)
        await ctx.send(f"🔊 Volumen ajustado a {volume}%")
