from __future__ import annotations

import traceback
from logging import DEBUG, getLogger
from os import getenv
from typing import TYPE_CHECKING, Any

import disnake
from disnake.ext import commands
from mafic import NodePool, Player, Playlist, Track, TrackEndEvent



getLogger("mafic").setLevel(DEBUG)


class Bot(commands.InteractionBot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.ready_ran = False
        self.pool = NodePool(self)

    async def on_ready(self):
        if self.ready_ran:
            return

        await self.pool.create_node(
            host="127.0.0.1",
            port=2333,
            label="MAIN",
            password="youshallnotpass",
        )
        print("Connected.")

        self.ready_ran = True


bot = Bot(intents=disnake.Intents.all())


class MyPlayer(Player[Bot]):
    def __init__(self, client: Bot, channel: disnake.VoiceChannel) -> None:
        super().__init__(client, channel)

        # Mafic does not provide a queue system right now, low priority.
        self.queue: list[Track] = []


@bot.slash_command(dm_permission=False)
async def join(inter: disnake.GuildCommandInteraction):
    """Join your voice channel."""
    

    if not inter.author.voice or not inter.author.voice.channel:
        return await inter.response.send_message("You are not in a voice channel.")

    channel = inter.author.voice.channel

    # This apparently **must** only be `Client`.
    await channel.connect(cls=MyPlayer)  # pyright: ignore[reportGeneralTypeIssues]
    await inter.send(f"Joined {channel.mention}.")


@bot.slash_command(dm_permission=False)
async def play(inter: disnake.GuildCommandInteraction, query: str):
    """Play a song.

    query:
        The song to search or play.
    """
    

    if not inter.guild.voice_client:
        await join(inter)

    player: MyPlayer = (
        inter.guild.voice_client
    )  # pyright: ignore[reportGeneralTypeIssues]

    tracks = await player.fetch_tracks(query)
    if not tracks:
        return await inter.send("No tracks found.")

    if isinstance(tracks, Playlist):
        tracks = tracks.tracks
        if len(tracks) > 1:
            player.queue.extend(tracks[1:])
    
    track = tracks[0]
    

    await player.play(track)
        
    await inter.send(f"Playing [{track.title}]({track.uri})")

@bot.slash_command(description="Stop the music")
async def stop(inter:disnake.GuildCommandInteraction):
    try:
        await inter.guild.voice_client.disconnect()
        
        
        await inter.send("Disconnected.", ephemeral=True)
    except:
        await inter.send("Not disconnected.", ephemeral=True)
    try:
        await inter.guild.voice_client.cleanup()
    except:
        pass
@bot.listen()
async def on_track_end(event: TrackEndEvent):
    assert isinstance(event.player, MyPlayer)

    if event.player.queue:
        await event.player.play(event.player.queue.pop(0))
    


    
@bot.event
async def on_slash_command_error(inter: disnake.AppCmdInter, error: Exception):
    traceback.print_exception(type(error), error, error.__traceback__)
    await inter.send(f"An error occurred: {error}")




bot.run("token here")
