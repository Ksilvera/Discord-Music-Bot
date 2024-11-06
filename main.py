import discord
from discord.ext import commands
import os, asyncio

from help import help
from music import music

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

bot.remove_command('help')

async def main():
    async with bot:
        await bot.add_cog(help(bot))
        await bot.add_cog(music(bot))
        await bot.start(os.getenv['discord_token'])

asyncio.run(main())