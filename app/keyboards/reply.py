from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="✍️ Telefon raqamni yozish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def get_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥥 Boshqa mahsulotlar")],
            [KeyboardButton(text="🔻 Vazn yo'qotish"), KeyboardButton(text="🔺 Vazn olish")],
            [KeyboardButton(text="📦 Mening buyurtmalarim")]
        ],
        resize_keyboard=True
    )
    return keyboard
