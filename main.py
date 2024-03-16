import asyncio

import aiogram.client.default
from aiogram import Dispatcher, Bot, Router

from aiogram.filters import CommandStart
from aiogram.types import *
from aiogram.client.default import DefaultBotProperties

bot = None
dp = Dispatcher()

props = DefaultBotProperties()
props.parse_mode = 'html'

@dp.message(CommandStart)
async def start(mess: Message):
    await mess.answer("<b>hello world!</b>")

async def main() -> None:
    global bot
    TOKEN = input("Enter your telegram bot token: ")
    bot = Bot(TOKEN, default=props)
    print('token fetched, bot initialized')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())