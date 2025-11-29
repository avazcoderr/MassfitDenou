from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.engine import async_session_maker
from app.database.requests import get_user_by_tg_id, create_user, update_user_phone
from app.keyboards.reply import get_phone_keyboard, get_main_menu_keyboard
from app.keyboards.inline import get_admin_panel_keyboard
from app.config import ADMIN_ID
import re

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


@router.message(Command('start'))
async def cmd_start(message: Message):
    # Check if user is admin
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer(
            "🔐 <b>Admin Panelga xush kelibsiz</b>\n\n"
            "Bu yerda siz mahsulotlarni boshqarishingiz va statistikani ko'rishingiz mumkin.\n"
            "Quyidagi variantlardan birini tanlang:",
            reply_markup=get_admin_panel_keyboard()
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
    await message.answer(
        "✍️ <b>Telefon raqamini kiriting</b>\n\n"
        "Iltimos, telefon raqamingizni +998 XX XXX XXXX formatida kiriting.\n\n"
        "Masalan: +998 90 123 4567",
        reply_markup=None
    )
    await state.set_state(PhoneStates.waiting_for_phone)


@router.message(PhoneStates.waiting_for_phone)
async def process_manual_phone(message: Message, state: FSMContext):
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
        "🥗 <b>MassFit - Shaxsiy ovqatlanish yordamchingizga xush kelibsiz!</b>\n\n"
        "Biz sizga to'g'ri ovqatlanish orqali salomatlik va fitnes maqsadlaringizga erishishda yordam beramiz. "
        "Bizning bot sizning ehtiyojlaringizga moslashtirilgan shaxsiy ovqatlanish rejalari va professional tavsiyalarni taqdim etadi.\n\n"
        "✨ <b>Biz taklif qilamiz:</b>\n"
        "• Vazn yo'qotish yoki mushak massasini oshirish uchun maxsus ovqatlanish rejalari\n"
        "• Muvozanatli ovqatlanish bo'yicha tavsiyalar\n"
        "• Sog'lom retseptlar va ovqatlanish g'oyalari\n"
        "• Professional parhez bo'yicha yo'riqnoma\n"
        "• Buyurtmalaringiz va taraqqiyotingizni kuzatish\n\n"
        "Boshlash uchun maqsadingizni tanlang! 👇"
    )
    
    await message.answer(
        bot_description,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
