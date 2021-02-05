import aiocron
import aiohttp
import discord
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.WARNING)

TECH_DIFFICULTIES_MSG = """Sorry, I couldn't complete that command. Please try
again later or contact an administrator."""

client = discord.Client()

async def get_daily_puzzle():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.chess.com/pub/puzzle') as r:
            if r.status == 200:
                return await r.json()

async def post_daily_puzzle(channel):
    try:
        json = await get_daily_puzzle()
        date = datetime.utcfromtimestamp(json['publish_time']).strftime('%A %Y.%m.%d')
        title = json['title']
        img_url = json['image'] + "&coordinates=true"
        fen = json['fen']
        if (fen.split(' ')[1]) == 'b':
            img_url += '&flip=true'
        await channel.send(f'Daily Puzzle: {date} - {title}')
        await channel.send(img_url)
    except Exception as e:
        logging.exception(e)
        await channel.send(TECH_DIFFICULTIES_MSG)

async def post_daily_puzzle_link(channel):
    try:
        json = await get_daily_puzzle()
        link = json['url']
        await channel.send(f'<{link}>')
    except Exception as e:
        logging.exception(e)
        await channel.send(TECH_DIFFICULTIES_MSG)

async def post_daily_puzzle_solution(channel):
    try:
        json = await get_daily_puzzle()
        pgn = json['pgn']
        solution = pgn.split('\r\n\r\n')[1]
        await channel.send(solution)
    except Exception as e:
        logging.exception(e)
        await channel.send(TECH_DIFFICULTIES_MSG)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!help'):
        await message.channel.send(
"""I'll post the daily puzzle from chess.com every day at 9am.

commands: !puzzle, !link, !solution""")

    if message.content.startswith('!puzzle'):
        await post_daily_puzzle(message.channel)

    if message.content.startswith('!link'):
        await post_daily_puzzle_link(message.channel)

    if message.content.startswith('!solution'):
        await post_daily_puzzle_solution(message.channel)

@aiocron.crontab(os.getenv('CRON_SCHEDULE'))
async def scheduled_post_daily_puzzle():
    channel = client.get_channel(int(os.getenv('CHANNEL_ID')))
    await post_daily_puzzle(channel)

client.run(os.getenv('TOKEN'))
