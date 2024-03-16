import asyncio
from groupparser import GroupParser
from inlinekeyboardgenerator import InlineKeyboardGenerator
from aiogram import Dispatcher, Bot

from aiogram.filters import CommandStart
from aiogram.types import *
from aiogram.client.default import DefaultBotProperties
import requests

bot = None
dp = Dispatcher()

props = DefaultBotProperties()
props.parse_mode = 'html'

parser = GroupParser()
kb_generator = InlineKeyboardGenerator()


@dp.message(CommandStart)
async def start(mess: Message):
    chat_id = mess.chat.id
    django_response = requests.get(f'http://127.0.0.1:8000/api/get_group/?chatId={chat_id}')
    if django_response.status_code == 200:
        await mess.answer('welcome!')
    elif django_response.status_code == 404:
        opi_response = requests.get('http://80.78.253.10/api/schedule')
        if opi_response.status_code != 200:
            await mess.answer(opi_response.text + '\n error of fetching schedule')
            return
        schedule_json = opi_response.json()
        groupdata_list = parser.getGroupCodesList(schedule_json)
        markup = kb_generator.generateKeyboardByGroupDataList(groupdata_list)

        await mess.answer('Для того чтобы пользоваться ботом, выберите свою группу', reply_markup=markup)
    else:
        await mess.answer(str(django_response) + 'ошибка')

@dp.callback_query(lambda call: call.data.startswith('code_'))
async def callback_query(call: CallbackQuery):
    mess = call.message
    code = call.data[5:]
    body = {'chatId': str(mess.chat.id), 'groupId': str(code)}
    post_response = requests.post('http://127.0.0.1:8000/api/set_group/', json=body)
    if post_response.status_code != 201:
        await mess.answer('Ошибка' + str(post_response.status_code))
        await call.answer()
        return
    await call.answer()
    await mess.answer('успешная регистрация')



async def main() -> None:
    global bot
    TOKEN = input("Enter your telegram bot token: ")

    bot = Bot(TOKEN, default=props)
    print('token fetched, bot initialized')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())