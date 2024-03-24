import asyncio

import typing_extensions

from group_parser import GroupParser
from inline_keyboard_generator import InlineKeyboardGenerator
from aiogram import Dispatcher, Bot, Router, F
from pdf_utils import PdfUtils
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
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
str_bachelor = 'Бакалавриат'
str_masters = 'Магистратура'
str_full_time = 'Очная'
str_part_time = 'Очно-заочная'

valid_options_degree = [str_bachelor, str_masters]
valid_options_study_form = [str_full_time, str_part_time]

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
        [InlineKeyboardButton(text=str_disk,
                              url='https://disk.yandex.ru/d/X1mkmFS9TpJJiw')],

        [
            InlineKeyboardButton(text=str_emit,
                                 url='https://emit.ranepa.ru/faculty-2/ai/'),
            InlineKeyboardButton(text=str_opi, url='https://opi-emit.ru/')
        ],
        [
            InlineKeyboardButton(text=str_profile,
                                 url='https://emit.ranepa.ru/faculty-2/ai/'),
            InlineKeyboardButton(text=str_support, url='https://opi-emit.ru/')
        ],

    ]
)


class BotStates(StatesGroup):
    reg_degree = State()
    reg_study_form = State()
    reg_course = State()
    reg_group = State()
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
        await mess.answer(
            'чтобы пользоваться ботом необходимо зарегистрироваться')
        await mess.answer(
            'Ты учишься на бакалавриате или магистратуре?',
            reply_markup=ReplyKeyboardMarkup(
                resize_keyboard=True,
                keyboard=[[KeyboardButton(text=str_bachelor)],
                          [KeyboardButton(text=str_masters)]]
            ))
        await state.set_state(BotStates.reg_degree)
        return
        # await mess.answer(f'{mess.chat.id}')
        # groupdata_list = get_groupdata_list()
        # if groupdata_list is None:
        #     await mess.answer('error of fetching schedule')
        #     return
        #
        # markup = kb_generator.generate_keyboard_by_group_data_list(groupdata_list)
        # await mess.answer('Для того чтобы пользоваться ботом, выберите свою группу', reply_markup=markup)
        # return

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


def get_groupdata_list(data: dict):
    opi_response = requests.get('http://80.78.253.10/api/schedule')
    if opi_response.status_code != 200:
        return None
    groups_json = opi_response.json()
    groupdata_list = parser.get_group_codes_list(groups_json)
    return groupdata_list


@router.message(
    BotStates.reg_degree,
    F.text.in_(valid_options_degree)
)
async def degree_chosen(mess: Message, state: FSMContext):
    degree = 'bachelor' if mess.text == str_bachelor else 'magister'
    await state.update_data(degree=degree)
    await state.set_state(BotStates.reg_study_form)
    await mess.answer(
        'На какой форме обучения?',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[[KeyboardButton(text=str_full_time),
                       KeyboardButton(text=str_part_time)]]
        )
    )


@router.message(BotStates.reg_degree)
async def degree_invalid(mess: Message):
    await mess.answer(
        'Похоже вы выбрали несуществующую опцию. '
        'Воспользуйтесь кнопками и попробуйте ещё раз')


@router.message(
    BotStates.reg_study_form,
    F.text.in_(valid_options_study_form)
)
async def study_form_chosen(mess: Message, state: FSMContext):
    form = 'full-time' if mess.text == str_full_time else 'part-time'
    await state.update_data(study_form=form)
    await state.set_state(BotStates.reg_course)
    course_num = 4 if mess.text == str_full_time else 5

    await mess.answer(
        'На каком курсе?',
        reply_markup=generate_courses_kb(course_num)
    )
def generate_courses_kb(course_num):
    kb = ReplyKeyboardBuilder()
    for i in range(1, course_num + 1):
        kb.add(KeyboardButton(text=str(i) + ' курс'))

    kb.adjust(2, 2)
    markup = kb.as_markup()
    markup.resize_keyboard = True
    markup.one_time_keyboard = True
    return markup

@router.message(BotStates.reg_study_form)
async def study_form_invalid(mess: Message):
    await mess.answer('Похоже вы выбрали несуществующую опцию. '
                      'Воспользуйтесь кнопками и попробуйте ещё раз')


@router.message(BotStates.reg_course,
                F.text.in_([str(i) + ' курс' for i in range(1, 5 + 1)]))
async def course_chosen(mess: Message, state: FSMContext):
    data = await state.get_data()

    course = int(mess.text[0])
    form = data['study_form']
    if form == str_full_time and course == 5:
        await mess.answer('Похоже вы выбрали несуществующую опцию. '
                          'Воспользуйтесь кнопками и попробуйте ещё раз',
                          reply_markup=generate_courses_kb(course-1))
        return

    await state.update_data(course=course)
    await state.set_state(BotStates.reg_group)
    groupdata_list = get_groupdata_list(await state.get_data())
    if groupdata_list is None:
        await mess.answer('error of fetching schedule')
        return
    markup = kb_generator.generate_keyboard_by_group_data_list(groupdata_list)
    await mess.answer('Выберите вашу группу', reply_markup=markup)


@router.message(BotStates.reg_course)
async def course_invalid(mess: Message, state: FSMContext):
    study_form = (await state.get_data())['study_form']
    course_num = 4 if study_form == str_full_time else 5
    await mess.answer('Похоже вы выбрали несуществующую опцию. '
                      'Воспользуйтесь кнопками и попробуйте ещё раз',
                      reply_markup=generate_courses_kb(course_num))


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
    # здесь костыль с менюшками
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
    chat_id = mess.chat.id
    requests.get(f'http://127.0.0.1:8000/api/delete_group/?chatId={chat_id}')
    await state.update_data({})
    await state.set_state(BotStates.reg_degree)
    await mess.answer(
        'Ты учишься на бакалавриате или магистратуре?',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[[KeyboardButton(text=str_bachelor)],
                      [KeyboardButton(text=str_masters)]]
        ))


@dp.callback_query(lambda call: call.data.startswith('code_'))
async def reg_callback(call: CallbackQuery, state: FSMContext):
    mess = call.message
    code = call.data[5:]
    await state.update_data(group_code=code)

    response_status = post_user_data(mess, (await state.get_data()))

    if response_status != 201:
        await mess.answer(f'{code}')
        await mess.answer('Ошибка' + str(response_status))
        await call.answer()
        return
    await call.answer()
    await mess.edit_text(f'Выбрана группа <b>{code}</b>')
    await mess.answer('Регистрация завершена!')
    await state.set_state(BotStates.root)
    await mess.answer('Главное меню', reply_markup=main_menu)

def post_user_data(mess: Message, data: dict):
    body = {
        'chatId': str(mess.chat.id),
        'groupId': data['group_code'],
        'degree': data['degree'],
        'studyForm': data['study_form'],
        'course': data['course']
    }

    post_response = requests.post('http://127.0.0.1:8000/api/set_data/',
                                  json=body)
    if post_response.status_code != 201:
        return post_response.status_code
    return 201

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
            media_group.add(type='photo',
                            media=FSInputFile(os.path.join(folder, filename)))
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