from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
from app.database.engine import async_session_maker
from app.database.requests import get_user_by_tg_id, create_user, update_user_phone
from app.keyboards.reply import get_phone_keyboard, get_main_menu_keyboard
from app.keyboards.inline import get_admin_panel_keyboard
from app.config import is_admin, CHANNEL_ID, ENABLE_SUBSCRIPTION_CHECK
import re
import logging

router = Router()


class PhoneStates(StatesGroup):
    waiting_for_phone = State()


def validate_uzbekistan_phone(phone: str) -> bool:
    """Validate Uzbekistan phone number format"""
    # Remove all spaces and dashes
    phone = re.sub(r'[\s\-]', '', phone)
    
    # Check if starts with +998 and has correct length (13 characters total)
    if phone.startswith('+998') and len(phone) == 13:
        # Check if remaining 9 digits are all numbers
        return phone[4:].isdigit()
    
    return False


def format_uzbekistan_phone(phone: str) -> str:
    """Format phone number to standard +998 XX XXX XXXX format"""
    phone = re.sub(r'[\s\-]', '', phone)
    if phone.startswith('+998') and len(phone) == 13:
        return f"+998 {phone[4:6]} {phone[6:9]} {phone[9:13]}"
    return phone


async def check_subscription(bot, user_id: int) -> bool:
    """Check if user is subscribed to the channel"""
    if not ENABLE_SUBSCRIPTION_CHECK:
        return True  # Subscription checking is disabled
        
    if not CHANNEL_ID:
        return True  # If no channel ID is set, allow access
    
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ['creator', 'administrator', 'member']
    except TelegramAPIError as e:
        logging.error(f"Error checking subscription for user {user_id}: {e}")
        # Return False to enforce subscription when there's an error
        # This ensures users must subscribe even if we can't verify
        return False


def get_subscription_keyboard():
    """Get keyboard for subscription request"""
    # For channel IDs starting with -100, we need to construct the URL differently
    if CHANNEL_ID and CHANNEL_ID.startswith('-100'):
        # Remove -100 prefix to get the actual channel identifier
        channel_identifier = CHANNEL_ID[4:]
        channel_url = f"https://t.me/c/{channel_identifier}"
    else:
        # If it's a username or different format
        channel_url = f"https://t.me/{CHANNEL_ID.lstrip('@')}" if CHANNEL_ID else "https://t.me/"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=channel_url)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")]
    ])
    return keyboard


@router.message(Command('start'))
async def cmd_start(message: Message):
    # Check if user is admin
    if is_admin(message.from_user.id):
        await message.answer(
            "🔐 <b>Admin Panelga xush kelibsiz</b>\n\n"
            "Bu yerda siz mahsulotlarni boshqarishingiz va statistikani ko'rishingiz mumkin.\n"
            "Quyidagi variantlardan birini tanlang:",
            reply_markup=get_admin_panel_keyboard()
        )
        return
    
    # Check subscription for regular users
    bot = message.bot
    is_subscribed = await check_subscription(bot, message.from_user.id)
    
    if not is_subscribed:
        await message.answer(
            "🔒 <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
            "Bizning kanalimizga obuna bo'lib, botning barcha imkoniyatlaridan foydalaning.\n\n"
            "Obuna bo'lgandan keyin \"✅ Tekshirish\" tugmasini bosing.",
            reply_markup=get_subscription_keyboard()
        )
        return
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        
        if not user:
            # Create new user
            full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            await create_user(
                session,
                tg_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                full_name=full_name
            )
            
            await message.answer(
                "Assalomu alaykum! Telefon raqamingizni yuboring.\n\n"
                "📱 Kontakt yuborish tugmasini bosing yoki\n"
                "✍️ Qo'lda yozish tugmasini bosing.\n\n"
                "Bu siz bilan bog'lanishimiz uchun kerak.",
                reply_markup=get_phone_keyboard()
            )
        elif not user.phone_number:
            # User exists but no phone number
            await message.answer(
                "Assalomu alaykum! Telefon raqamingizni yuboring.\n\n"
                "📱 Kontakt yuborish tugmasini bosing yoki\n"
                "✍️ Qo'lda yozish tugmasini bosing.\n\n"
                "Bu siz bilan bog'lanishimiz uchun kerak.",
                reply_markup=get_phone_keyboard()
            )
        else:
            # User exists with phone number - show main menu
            await show_main_menu(message)


@router.message(F.text == "✍️ Telefon raqamni yozish")
async def request_manual_phone(message: Message, state: FSMContext):
    # Check subscription before allowing manual phone input
    if not is_admin(message.from_user.id):
        bot = message.bot
        is_subscribed = await check_subscription(bot, message.from_user.id)
        
        if not is_subscribed:
            await message.answer(
                "🔒 <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
                "Bizning kanalimizga obuna bo'lib, botning barcha imkoniyatlaridan foydalaning.\n\n"
                "Obuna bo'lgandan keyin \"✅ Tekshirish\" tugmasini bosing.",
                reply_markup=get_subscription_keyboard()
            )
            return
    
    await message.answer(
        "✍️ <b>Telefon raqamini kiriting</b>\n\n"
        "Iltimos, telefon raqamingizni +998 XX XXX XXXX formatida kiriting.\n\n"
        "Masalan: +998 90 123 4567",
        reply_markup=None
    )
    await state.set_state(PhoneStates.waiting_for_phone)


@router.message(PhoneStates.waiting_for_phone)
async def process_manual_phone(message: Message, state: FSMContext):
    # Check subscription before processing manual phone
    if not is_admin(message.from_user.id):
        bot = message.bot
        is_subscribed = await check_subscription(bot, message.from_user.id)
        
        if not is_subscribed:
            await message.answer(
                "🔒 <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
                "Bizning kanalimizga obuna bo'lib, botning barcha imkoniyatlaridan foydalaning.\n\n"
                "Obuna bo'lgandan keyin \"✅ Tekshirish\" tugmasini bosing.",
                reply_markup=get_subscription_keyboard()
            )
            await state.clear()
            return
    
    phone = message.text.strip()
    
    if not validate_uzbekistan_phone(phone):
        await message.answer(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "Iltimos, telefon raqamni to'g'ri formatda kiriting:\n"
            "+998 XX XXX XXXX\n\n"
            "Masalan: +998 90 123 4567"
        )
        return
    
    formatted_phone = format_uzbekistan_phone(phone)
    
    async with async_session_maker() as session:
        await update_user_phone(session, message.from_user.id, formatted_phone)
    
    await state.clear()
    await show_main_menu(message)


@router.message(F.contact)
async def process_contact(message: Message, state: FSMContext):
    # Check subscription before processing contact
    if not is_admin(message.from_user.id):
        bot = message.bot
        is_subscribed = await check_subscription(bot, message.from_user.id)
        
        if not is_subscribed:
            await message.answer(
                "🔒 <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>\n\n"
                "Bizning kanalimizga obuna bo'lib, botning barcha imkoniyatlaridan foydalaning.\n\n"
                "Obuna bo'lgandan keyin \"✅ Tekshirish\" tugmasini bosing.",
                reply_markup=get_subscription_keyboard()
            )
            return
    
    phone_number = message.contact.phone_number
    
    # Format the phone number if it's valid
    if validate_uzbekistan_phone(phone_number):
        phone_number = format_uzbekistan_phone(phone_number)
    
    async with async_session_maker() as session:
        await update_user_phone(session, message.from_user.id, phone_number)
    
    await state.clear()
    await show_main_menu(message)


async def show_main_menu(message: Message):
    bot_description = (
        "<b>🌿 MassFit - <u>Shaxsiy ovqatlanish yordamchingizga</u> xush kelibsiz!</b>\n\n"
        "Biz sizga to'g'ri ovqatlanish orqali sog'lom turmush tarzi va fitness maqsadlaringizga erishishda yordam beramiz. "
        "Bizning bot sizning ehtiyojlaringizga moslashtirilgan shaxsiy ovqatlanish rejalarini "
        "va professional tavsiyalarni taqdim etadi.\n\n"
        "<b>✨ <u>Biz taklif qilamiz:</u></b>\n"
        "• 🍽 <b>Vazn yo'qotish</b> yoki <b>mushak massasini oshirish</b> uchun maxsus ovqatlanish rejalar  \n"
        "• 🥦 Muvozanatli ovqatlanish bo'yicha tavsiyalar  \n"
        "• 🥗 <u>Sog'lom retseptlar</u> va ovqatlanish g'oyalari  \n"
        "• 📋 Professional parhez bo'yicha <u>yo'riqnoma</u>  \n\n"
        "<b>👇 <u>Boshlash uchun maqsadingizni tanlang!</u></b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🔒 Sifat kafolati:</b>  \n"
        "MassFit mahsulotlari sifati — <b>JasurBarber</b> tomonidan to'liq kafolatlanadi.  \n"
        "💯 Halol, organik va sinovdan o'tgan mahsulotlar!"
    )
    await message.answer(
        bot_description,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    """Handle subscription check callback"""
    bot = callback.bot
    is_subscribed = await check_subscription(bot, callback.from_user.id)
    
    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali kanalga obuna bo'lmagan ekansiz. Iltimos, avval kanalga obuna bo'ling!",
            show_alert=True
        )
        return
    
    await callback.answer("✅ Tabriklaymiz! Siz kanalga obuna bo'ldingiz.", show_alert=True)
    await callback.message.delete()
    
    # Now proceed with the normal start flow
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        
        if not user:
            # Create new user
            full_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
            await create_user(
                session,
                tg_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
                full_name=full_name
            )
            
            await callback.message.answer(
                "Assalomu alaykum! Telefon raqamingizni yuboring.\n\n"
                "📱 Kontakt yuborish tugmasini bosing yoki\n"
                "✍️ Qo'lda yozish tugmasini bosing.\n\n"
                "Bu siz bilan bog'lanishimiz uchun kerak.",
                reply_markup=get_phone_keyboard()
            )
        elif not user.phone_number:
            # User exists but no phone number
            await callback.message.answer(
                "Assalomu alaykum! Telefon raqamingizni yuboring.\n\n"
                "📱 Kontakt yuborish tugmasini bosing yoki\n"
                "✍️ Qo'lda yozish tugmasini bosing.\n\n"
                "Bu siz bilan bog'lanishimiz uchun kerak.",
                reply_markup=get_phone_keyboard()
            )
        else:
            # User exists with phone number - show main menu
            await show_main_menu(callback.message)
