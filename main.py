import asyncio
from group_parser import GroupParser
from inline_keyboard_generator import InlineKeyboardGenerator
from aiogram import Dispatcher, Bot, Router, F
from pdf_utils import PdfUtils
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.media_group import MediaGroupBuilder
import requests
import os

bot = None
dp = Dispatcher()
router = Router()
props = DefaultBotProperties()
props.parse_mode = 'html'

parser = GroupParser()
kb_generator = InlineKeyboardGenerator()

str_my_schedule = 'Получить моё расписание'
str_other_schedules = 'Получить расписание другой группы'
str_misc = 'Дополнительно'
str_back = 'Назад'
str_links = 'Полезные ссылки'
str_drop_user = 'Пройти регистрацию заново'
str_disk = 'Яндекс.Диск'
str_emit = 'Сайт ЭМИТа'
str_opi = 'Сайт ОПИ'
str_profile = 'Личный кабинет'
str_sdo = 'Кабинет в СДО'
str_vk_group = 'Группа в ВК'
str_support = 'Психологическая служба'

main_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,

    keyboard=[
        [
            KeyboardButton(text=str_my_schedule),
            KeyboardButton(text=str_other_schedules)
        ],
        [
            KeyboardButton(text=str_misc)
        ]
    ]
)

misc_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text=str_links),
            KeyboardButton(text=str_drop_user)
        ],
        [
            KeyboardButton(text=str_back)
        ]
    ]
)

links_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=str_back, callback_data='links_misc')],
        [InlineKeyboardButton(text=str_disk, url='https://disk.yandex.ru/d/X1mkmFS9TpJJiw')],

        [
            InlineKeyboardButton(text=str_emit, url='https://emit.ranepa.ru/faculty-2/ai/'),
            InlineKeyboardButton(text=str_opi, url='https://opi-emit.ru/')
         ],
        [
            InlineKeyboardButton(text=str_profile, url='https://emit.ranepa.ru/faculty-2/ai/'),
            InlineKeyboardButton(text=str_support, url='https://opi-emit.ru/')
         ],

    ]
)

class BotStates(StatesGroup):
    reg_degree = State()
    reg_study_form = State()
    reg_course = State()

    my_schedule = State()
    other_schedule = State()
    misc = State()
    links = State()
    root = State()

@router.message(CommandStart())
async def start(mess: Message, state: FSMContext):
    reg_response = is_user_registered(mess)
    print(reg_response)
    if reg_response is None:
        await mess.answer(f'wrong request')
        return

    if not reg_response:
        await mess.answer(f'{mess.chat.id}')
        groupdata_list = get_groupdata_list()
        if groupdata_list is None:
            await mess.answer('error of fetching schedule')
            return

        markup = kb_generator.generate_keyboard_by_group_data_list(groupdata_list)
        await mess.answer('Для того чтобы пользоваться ботом, выберите свою группу', reply_markup=markup)
        return

    await state.update_data(group_code=reg_response)
    await state.set_state(BotStates.root)
    await mess.answer('Добро пожаловать!')
    await mess.answer('Главное меню', reply_markup=main_menu)


def is_user_registered(mess: Message):
    chat_id = mess.chat.id
    django_response = requests.get(
        f'http://127.0.0.1:8000/api/get_group/?chatId={chat_id}')
    if django_response.status_code == 200:
        return django_response.json()['groupId']
    elif django_response.status_code == 404:
        return False
    else:
        return

def get_groupdata_list():
    opi_response = requests.get('http://80.78.253.10/api/schedule')
    if opi_response.status_code != 200:
        return None
    groups_json = opi_response.json()
    groupdata_list = parser.get_group_codes_list(groups_json)
    return groupdata_list


@router.message(
    BotStates.root,
    F.text == str_my_schedule
    )
async def get_my_schedule(mess: Message, state: FSMContext):
    group_code = await state.get_data()
    await mess.answer('Подождите, пожалуйста, скачиваю расписание...')
    await send_images(group_code['group_code'], mess)

@router.message(
    BotStates.root,
    F.text == str_other_schedules
    )
async def root_other_schedules_options(mess: Message, state: FSMContext):
    await mess.answer('Выбери группу, расписание которой хочешь получить')
    pass

@router.message(
    BotStates.root,
    F.text == str_misc
    )
async def root_misc(mess: Message, state: FSMContext):
    await state.set_state(BotStates.misc)
    await mess.answer('Дополнительно', reply_markup=misc_menu)

@router.message(BotStates.misc,
                F.text == str_links)
async def root_links(mess: Message, state: FSMContext):
    await state.set_state(BotStates.links)
    #здесь костыль с менюшками
    await mess.answer('полезные ссылки (+менюшка)', reply_markup=links_menu)


@router.message(BotStates.misc,
                F.text == str_back
                )
async def misc_root(mess: Message, state: FSMContext):
    await state.set_state(BotStates.root)
    await mess.answer('Главное меню', reply_markup=main_menu)

@router.message(BotStates.misc,
                F.text == str_drop_user)
async def misc_drop(mess: Message, state: FSMContext):
    await state.set_data({})
    await mess.answer('Ты уже у нас учишься или поступаешь?')
    await state.set_state(BotStates.reg_degree)

@dp.callback_query(lambda call: call.data.startswith('code_'))
async def reg_callback(call: CallbackQuery):
    mess = call.message
    code = call.data[5:]

    body = {'chatId': str(mess.chat.id), 'groupId': str(code)}
    post_response = requests.post('http://127.0.0.1:8000/api/set_group/', json=body)
    if post_response.status_code != 201:
        await mess.answer(f'{code}')
        await mess.answer('Ошибка' + str(post_response.status_code))
        await call.answer()
        return
    await call.answer()
    await mess.edit_text(f'<b>Выбрана группа {code}</b>')
    await mess.answer('успешная регистрация')

@router.callback_query(lambda call: call.data == 'links_misc')
async def misc_callback(call: CallbackQuery, state: FSMContext):
    mess = call.message
    await state.set_state(BotStates.misc)
    await mess.delete()
    await mess.answer(str_misc, reply_markup=misc_menu)


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
    dp.include_router(router)
    print('token fetched, bot initialized')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())