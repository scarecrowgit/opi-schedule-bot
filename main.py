import asyncio
import urllib3


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

valid_options_bachelor_full = [f'{i} курс' for i in range(0, 4 + 1)]
valid_options_bachelor_part = [f'{i} курс' for i in range(0, 5 + 1)]
valid_options_masters_full = [f'{i} курс' for i in range(0, 2 + 1)]

main_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    is_persistent=True,
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


class Navigation(StatesGroup):
    my_schedule = State()
    other_schedule = State()
    misc = State()
    links = State()
    root = State()


class Form(StatesGroup):
    degree = State()

    bachelor_study_form = State()
    masters_study_form = State()

    bachelor_full_course = State()
    bachelor_part_course = State()
    masters_full_course = State()

    group = State()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@router.message(CommandStart())
async def start(mess: Message, state: FSMContext):
    reg_response = is_user_registered(mess)
    if reg_response is None:
        await mess.answer(f'wrong request')
        return
    if not reg_response:
        await state.set_state(Form.degree)
        await mess.answer(
            'чтобы пользоваться ботом необходимо зарегистрироваться')
        await mess.answer(
            'Вы учитесь на бакалавриате или магистратуре?',
            reply_markup=ReplyKeyboardMarkup(
                resize_keyboard=True,
                is_persistent=True,
                keyboard=[[KeyboardButton(text=str_bachelor)],
                          [KeyboardButton(text=str_masters)]]
            ))
        return
    await state.update_data(group_code=reg_response)
    await state.set_state(Navigation.root)
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
    Form.degree,
    F.text == str_bachelor
)
async def bachelor_chosen(mess: Message, state: FSMContext):
    await state.update_data(degree='bachelor')
    await state.set_state(Form.bachelor_study_form)

    await mess.answer(
        'На какой форме обучения?',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            is_persistent=True,
            keyboard=[[KeyboardButton(text=str_full_time),
                       KeyboardButton(text=str_part_time)]]
        )
    )


@router.message(
    Form.degree,
    F.text == str_masters
)
async def masters_chosen(mess: Message, state: FSMContext):
    await state.update_data(degree='magister')
    await state.set_state(Form.masters_study_form)

    await mess.answer(
        'На какой форме обучения?',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            is_persistent=True,
            keyboard=[[KeyboardButton(text=str_full_time)]]
        )
    )


@router.message(Form.degree)
async def degree_invalid(mess: Message):
    await mess.answer(
        'Похоже вы выбрали несуществующую опцию. '
        'Воспользуйтесь кнопками и попробуйте ещё раз')


@router.message(
    Form.bachelor_study_form,
    F.text == str_full_time
)
async def bachelor_full_chosen(mess: Message, state: FSMContext):
    await state.update_data(study_form='full-time')
    await state.set_state(Form.bachelor_full_course)
    course_num = 4
    await mess.answer(
        'На каком курсе?',
        reply_markup=generate_courses_kb(course_num)
    )


@router.message(
    Form.bachelor_study_form,
    F.text == str_part_time
)
async def bachelor_part_chosen(mess: Message, state: FSMContext):
    await state.update_data(study_form='part-time')
    await state.set_state(Form.bachelor_part_course)
    course_num = 5
    await mess.answer(
        'На каком курсе?',
        reply_markup=generate_courses_kb(course_num)
    )


@router.message(
    Form.masters_study_form,
    F.text == str_full_time
)
async def masters_full_chosen(mess: Message, state: FSMContext):
    await state.update_data(study_form='full-time')
    await state.set_state(Form.masters_full_course)
    course_num = 2
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
    markup.is_persistent = True

    return markup


@router.message(Form.bachelor_study_form)
@router.message(Form.masters_study_form)
async def study_form_invalid(mess: Message):
    await mess.answer('Похоже вы выбрали несуществующую опцию. '
                      'Воспользуйтесь кнопками и попробуйте ещё раз')


@router.message(Form.bachelor_full_course,
                F.text.in_(valid_options_bachelor_full)
                )
@router.message(Form.bachelor_part_course,
                F.text.in_(valid_options_bachelor_part)
                )
@router.message(Form.masters_full_course,
                F.text.in_(valid_options_masters_full)
                )
async def course_chosen(mess: Message, state: FSMContext):
    course = int(mess.text[0])
    await state.update_data(course=course)
    await state.set_state(Form.group)
    groupdata_list = get_groupdata_list()
    if groupdata_list is None:
        await mess.answer('error of fetching schedule')
        return
    data = await state.get_data()
    markup = kb_generator.generate_keyboard_by_group_data_list(
        groupdata_list,
        data)

    await mess.answer('Выберите группу', reply_markup=markup)

@router.message(Form.bachelor_full_course)
@router.message(Form.bachelor_part_course)
@router.message(Form.masters_full_course)
async def course_invalid(mess: Message):
    await mess.answer('Похоже вы выбрали несуществующую опцию. '
                      'Воспользуйтесь кнопками и попробуйте ещё раз')


@router.message(
    Navigation.root,
    F.text == str_my_schedule
)
async def get_my_schedule(mess: Message, state: FSMContext):
    data = await state.get_data()
    await mess.answer('Подождите, пожалуйста, скачиваю расписание...')
    await send_images(data['group_code'], mess)


@router.message(
    Navigation.root,
    F.text == str_other_schedules
)
async def root_other_schedules_options(mess: Message, state: FSMContext):
    await state.update_data(search_other=True)
    await state.set_state(Form.degree)
    await mess.answer(
        'Вы хотите получить расписание бакалавриата или магистратуры?',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            is_persistent=True,
            keyboard=[[KeyboardButton(text=str_bachelor)],
                      [KeyboardButton(text=str_masters)]]
        ))




@router.message(
    Navigation.root,
    F.text == str_misc
)
async def root_misc(mess: Message, state: FSMContext):
    await state.set_state(Navigation.misc)
    await mess.answer('Дополнительно', reply_markup=misc_menu)


@router.message(Navigation.misc,
                F.text == str_links)
async def root_links(mess: Message, state: FSMContext):
    await state.set_state(Navigation.links)
    # здесь костыль с менюшками
    await mess.answer('Полезные ссылки', reply_markup=links_menu)


@router.message(Navigation.misc,
                F.text == str_back
                )
async def misc_root(mess: Message, state: FSMContext):
    await state.set_state(Navigation.root)
    await mess.answer('Главное меню', reply_markup=main_menu)


@router.message(Navigation.misc,
                F.text == str_drop_user)
async def misc_drop(mess: Message, state: FSMContext):
    chat_id = mess.chat.id
    requests.get(f'http://127.0.0.1:8000/api/delete_data/?chatId={chat_id}')
    await state.update_data({})
    await state.set_state(Form.degree)
    await mess.answer(
        'Вы учитесь на бакалавриате или магистратуре?',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[[KeyboardButton(text=str_bachelor)],
                      [KeyboardButton(text=str_masters)]]
        ))


@dp.callback_query(lambda call: call.data.startswith('code_'))
async def reg_callback(call: CallbackQuery, state: FSMContext):
    mess = call.message
    code = call.data[5:]
    data = await state.get_data()
    try:
        if data['search_other']:

            my_group_code = (await state.get_data())['group_code']
            await state.set_data({'group_code': my_group_code})
            await mess.edit_text(f'Выбрана группа <b>{code}</b>')
            await mess.answer('Подождите, пожалуйста, скачиваю расписание...')
            await send_images(code, mess)
            await call.answer()
            await state.set_state(Navigation.root)
            await mess.answer('Главное меню', reply_markup=main_menu)
    except KeyError:

        await state.update_data({'group_code': code})

        response_status = post_user_data(mess, (await state.get_data()))

        if response_status != 201:
            await mess.answer(f'{code}')
            await mess.answer('Ошибка' + str(response_status))
            await call.answer()
            return
        await call.answer()
        await mess.edit_text(f'Выбрана группа <b>{code}</b>')
        await mess.answer('Регистрация завершена!')
        await state.set_state(Navigation.root)
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
    await state.set_state(Navigation.misc)
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
