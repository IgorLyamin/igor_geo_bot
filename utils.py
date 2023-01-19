from telegram import ReplyKeyboardMarkup


def get_kb():
    btns = [
        ['Добавить слой', 'Контакты админа'],
        # ['Контакты админа']
    ]
    return ReplyKeyboardMarkup(btns, resize_keyboard=True)
