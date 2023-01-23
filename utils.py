from telegram import ReplyKeyboardMarkup


def get_kb():
    btns = [
        ['Метро', 'Центр', 'Парк'],
        ['Старт']
    ]
    return ReplyKeyboardMarkup(btns, resize_keyboard=True)
