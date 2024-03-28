from aiogram.utils.keyboard import InlineKeyboardBuilder
from group_data import GroupData

class InlineKeyboardGenerator:
    def __init__(self):
        pass

    def generate_keyboard_by_group_data_list(
            self, groupdata_list: list[GroupData], data: dict):
        builder = InlineKeyboardBuilder()
        for item in groupdata_list:
            title = item.title
            code = item.group_code
            study_form = 'v' if data['study_form'] == 'part-time' else 'o'
            if (data['course'] == item.study_year
                    and data['degree'][0] == code[1]
                    and study_form == code[0]):
                builder.button(text=title, callback_data=f'code_{code}')
        return builder.adjust(2, repeat=True).as_markup()
