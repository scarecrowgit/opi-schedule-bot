import asyncio
from group_parser import GroupParser
from inline_keyboard_generator import InlineKeyboardGenerator
from aiogram import Dispatcher, Bot
from pdf_utils import PdfUtils
from aiogram.filters import CommandStart
from aiogram.types import *
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.media_group import MediaGroupBuilder
import requests
import os

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
        await mess.answer('Подождите, пожалуйста, скачиваю расписание...')
        group_code = django_response.json()['groupId']
        await send_images(group_code, mess)

    elif django_response.status_code == 404:
        opi_response = requests.get('http://80.78.253.10/api/schedule')
        if opi_response.status_code != 200:
            await mess.answer(opi_response.text + '\n error of fetching schedule')
            return
        schedule_json = opi_response.json()
        groupdata_list = parser.get_group_codes_list(schedule_json)
        markup = kb_generator.generate_keyboard_by_group_data_list(groupdata_list)

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
    await mess.edit_text('<b>Группа выбрана</b>')
    await mess.answer('успешная регистрация')

async def send_images(group_code, mess: Message):

    folder = PdfUtils.output_folder
    pdf_giver = PdfUtils(group_code)
    pdf_giver.create_image_from_pdf()
    file_names = os.listdir(folder)
    media_group = MediaGroupBuilder()
    for filename in file_names:
        if filename.endswith('png'):
            media_group.add(type='photo', media=FSInputFile(os.path.join(folder, filename)))
    await mess.answer_media_group(media=media_group.build())
    pdf_giver.clear_datas()


async def main() -> None:
    global bot
    # TOKEN = input("Enter your telegram bot token: ")
    TOKEN = '6973935650:AAGtwtcnOaeDGE40q5i4YiOOV5DJA_Byde8'

    bot = Bot(TOKEN, default=props)
    print('token fetched, bot initialized')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())