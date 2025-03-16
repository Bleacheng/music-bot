import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from collections import deque

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) # comment this line out once synced

SONG_QUEUES = {}

# handles concurrent execution of youtube searches
async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

# does the seraching
def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


# setup of intents (permissions for the bot)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# syncing up command tree as the bot initialises        
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()  # Sync all global commands
        print(f"Synced command tree globally.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    print(f"{bot.user} is online!")

@bot.tree.command(name="huzz", description="Displays the list of available commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Bot Commands", description="Here are the available commands:", colour=discord.Colour.teal())
    embed.add_field(name="/skuzz", value="Skips the current track.", inline=True)
    embed.add_field(name="/resuzz", value="Resumes playback if paused.", inline=True)
    embed.add_field(name="/puzz", value="Pauses the current track.", inline=True)
    embed.add_field(name="/pluzz", value="Plays a track or resumes playback.", inline=True)
    embed.add_field(name="/stuzz", value="Stops playback and clears the queue.", inline=True)
    embed.set_footer(text="Use these commands to control playback!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="skuzz", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        embed = discord.Embed(title="⏭ Skipped", description="Skipped the current song.", colour=discord.Colour.dark_gray())
    else:
        embed = discord.Embed(title="⚠️ Error", description="Not playing anything to skip.", colour=discord.Colour.red())
    await interaction.response.send_message(embed=embed)



@bot.tree.command(name="puzz", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        embed = discord.Embed(title="⚠️ Error", description="I'm not in a voice channel.", colour=discord.Colour.red())
        return await interaction.response.send_message(embed=embed)

    # Check if something is actually playing
    if not voice_client.is_playing():
        embed = discord.Embed(title="⚠️ Error", description="Nothing is currently playing.", colour=discord.Colour.red())
        return await interaction.response.send_message(embed=embed)
    
    # Pause the track
    voice_client.pause()
    embed = discord.Embed(title="⏸ Paused", description="Playback paused!", colour=discord.Colour.dark_gray())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="resuzz", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        embed = discord.Embed(title="⚠️ Error", description="I'm not in a voice channel.", colour=discord.Colour.red())
        return await interaction.response.send_message(embed=embed)

    # Check if it's actually paused
    if not voice_client.is_paused():
        embed = discord.Embed(title="⚠️ Error", description="I’m not paused right now.", colour=discord.Colour.red())
        return await interaction.response.send_message(embed=embed)
    
    # Resume playback
    voice_client.resume()
    embed = discord.Embed(title="⏸ Paused", description="Playback paused!", colour=discord.Colour.dark_gray())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stuzz", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        embed = discord.Embed(title="⚠️ Error", description="I'm not connected to any voice channel.", colour=discord.Colour.red())
    else:
        # Clear the guild's queue
        guild_id_str = str(interaction.guild_id)
        if guild_id_str in SONG_QUEUES:
            SONG_QUEUES[guild_id_str].clear()

        # If something is playing or paused, stop it
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        # (Optional) Disconnect from the channel
        await voice_client.disconnect()
        embed = discord.Embed(title="🛑 Stopped", description="Playback stopped and disconnected!", colour=discord.Colour.dark_gray())

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="quezz", description="Shows the current song queue.")
async def queue(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    if guild_id not in SONG_QUEUES or not SONG_QUEUES[guild_id]:
        embed = discord.Embed(title="🎵 Song Queue", description="The queue is currently empty.", colour=discord.Colour.dark_gray())
    else:
        embed = discord.Embed(title="🎵 Song Queue", colour=discord.Colour.dark_gray())
        for idx, (_, title) in enumerate(SONG_QUEUES[guild_id], start=1):
            embed.add_field(name=f"#{idx}", value=title, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pluzz", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play_command(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()
    
    voice_channel = interaction.user.voice.channel
    
    if voice_channel is None:
        embed = discord.Embed(title="⚠️ Error", description="You must be in a voice channel.", colour=discord.Colour.red())
        await interaction.followup.send(embed=embed)
        return

    voice_client = interaction.guild.voice_client
    
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)
        
    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }
    
    query = "ytsearch1:" + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])
    
    if tracks is None:
        embed = discord.Embed(title="⚠️ Error", description="No results found.", colour=discord.Colour.red())
        await interaction.followup.send(embed=embed)
        return

    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")
    
    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()
    
    SONG_QUEUES[guild_id].append((audio_url, title))
    
    embed = discord.Embed(title="🎶 Added to Queue", description=f"**{title}**", colour=discord.Colour.dark_gray())
    await interaction.followup.send(embed=embed)
    if not (voice_client.is_playing() or voice_client.is_paused()):
        await play_next_song(voice_client, guild_id, interaction.channel)
    
async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()
        
        ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k" #uses opus codec for streams which is a modern and efficient codec
        }
    
        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options) # FIXME executable="bin\\ffmpeg\ffmpeg.exe"
        
        def after_play(error):
            if error:
                print(f"Error playing song: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
        
        voice_client.play(source, after=after_play)
        embed = discord.Embed(title="🎶 Now Playing", description=f"**{title}**", colour=discord.Colour.dark_gray())
        asyncio.create_task(channel.send(embed=embed))
    
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()
# Start the bot with the token loaded from the .env file
bot.run(TOKEN)
