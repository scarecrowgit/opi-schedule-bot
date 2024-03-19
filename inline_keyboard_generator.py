from aiogram.utils.keyboard import InlineKeyboardBuilder
from group_data import GroupData

class InlineKeyboardGenerator:
    def __init__(self):
        pass

    def generate_keyboard_by_group_data_list(self, groupdata_list: list[GroupData]):
        builder = InlineKeyboardBuilder()
        for item in groupdata_list:
            title = item.title
            code = item.group_code
            builder.button(text=title, callback_data=f'code_{code}')
        return builder.adjust(3, repeat=True).as_markup()