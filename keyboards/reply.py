from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропуска"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пропустить")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_done_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура завершения отправки фото"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="/done")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def remove_keyboard() -> ReplyKeyboardMarkup:
    """Удаление клавиатуры"""
    return ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True, remove_keyboard=True)