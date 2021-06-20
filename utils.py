from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_keyboard():
    project_button = KeyboardButton('Текущий проект')
    say_hello_button = KeyboardButton('Познакомиться')
    meeting_button = KeyboardButton('Назначить встречу')
    status_button = KeyboardButton('Мой статус')
    my_keyboard = ReplyKeyboardMarkup([[project_button, say_hello_button],
                                       [meeting_button, status_button],
                                       ], resize_keyboard=True)
    return my_keyboard
