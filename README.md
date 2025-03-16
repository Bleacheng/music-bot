# huzzbot
this repo contains a script for a discord bot that plays music with stylised commands, using the discord.py library

## How to set up the bot so you can use it too 🐸
### Dependencies ###
`pip install discord.py`
`pip install python-dotenv`
`pip install yt-dlp`
`pip install PyNaCl`

**FFmpeg** will also be required to be installed https://www.ffmpeg.org/download.html
can be done by storing the executable file (.exe) in this folder structure: *bin/ffmpeg/ffmpeg.exe

Also create a discord bot by following this guide: https://discordpy.readthedocs.io/en/stable/discord.html

### Setup ###

Rename '.env.example' to '.env' and replace your_discord_token_here and your_guild_id_here like so:

DISCORD_TOKEN=your_discord_token_here
GUILD_ID=your_guild_id_here

This can be done in the following:

For DISCORD_TOKEN: 
1. Go to https://discord.com/developers/applications and make an account if you haven't already
2. Create a new Discord application
3. Settings > Bot > Token > Reset Token

For GUILD_ID:
1. Go to your server and ensure you are an admininistrator
2. Make sure developer mode is on 
3. Then to obtain the GUILD_ID: Server Settings > Widget > Server ID
4. Click "Copy ID" to get the server's GUILD_ID

Then save this and you can run your bot, YAY.
The gitignore should ignore this file so you don't leak info even by accident. 
This mainly applies to the DISCORD_TOKEN I realise, doesn't really apply to the GUILD_ID.

## How it works
basically yt-dlp searches for a song on youtube and creates a stream of it
FFMPEG uses that stream to play the audio on youtube

Use the '/huzz' command for a description of all commands :)

## Future improvements to be done
- Add Soundcloud and Spotify API support as well
