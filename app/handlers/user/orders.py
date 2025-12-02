from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.engine import async_session_maker
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from app.utils.formatters import format_price

router = Router()


class OrderStates(StatesGroup):
    waiting_for_delivery_location = State()
    waiting_for_text_address = State()


def get_address_from_coords(latitude: float, longitude: float) -> str:
    """Get address name from coordinates using reverse geocoding."""
    try:
        geolocator = Nominatim(user_agent="massfit_bot")
        location = geolocator.reverse(f"{latitude}, {longitude}", language="uz")
        if location and location.raw.get('address'):
            addr = location.raw['address']
            # Build short address from components
            parts = []
            
            # House number and road/street
            if addr.get('house_number'):
                parts.append(addr['house_number'])
            if addr.get('road'):
                parts.append(addr['road'])
            elif addr.get('street'):
                parts.append(addr['street'])
            
            # Neighborhood or suburb
            if addr.get('neighbourhood'):
                parts.append(addr['neighbourhood'])
            elif addr.get('suburb'):
                parts.append(addr['suburb'])
            
            # District
            if addr.get('city_district'):
                parts.append(addr['city_district'])
            
            if parts:
                return ", ".join(parts)
            return location.address
        return "Manzil aniqlanmadi"
    except GeocoderTimedOut:
        return "Manzil aniqlanmadi (timeout)"
    except Exception:
        return "Manzil aniqlanmadi"


@router.message(F.text == "📦 Mening buyurtmalarim")
async def my_orders(message: Message):
    from app.database.requests import get_user_by_tg_id
    from app.database.order_requests import get_basket_items
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        
        if not user:
            await message.answer("Foydalanuvchi topilmadi!")
            return
        
        basket_items = await get_basket_items(session, user.id)
        
        if not basket_items:
            await message.answer(
                "🛒 <b>Mening savatim</b>\n\n"
                "Savatingiz bo'sh.\n"
                "Buyurtma yaratish uchun mahsulotlarni savatga qo'shing!"
            )
            return
        
        # Calculate total
        total = 0
        items_text = ""
        
        for item in basket_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total += item_total
            items_text += f"• {product.name}\n  💰 {format_price(product.price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        text = (
            f"🛒 <b>Mening savatim</b>\n\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(total)} so'm</b>"
        )
        
        keyboard = []
        for item in basket_items:
            keyboard.append([
                InlineKeyboardButton(text="➖", callback_data=f"basket_dec_{item.product_id}_{item.quantity}"),
                InlineKeyboardButton(text=f"{item.product.name}: {item.quantity}", callback_data="basket_display"),
                InlineKeyboardButton(text="➕", callback_data=f"basket_inc_{item.product_id}_{item.quantity}")
            ])
        
        keyboard.append([InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order_prompt")])
        
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(F.data.startswith("basket_inc_"))
async def basket_increase(callback: CallbackQuery):
    from app.database.requests import get_user_by_tg_id
    from app.database.order_requests import update_basket_quantity, get_basket_items
    
    parts = callback.data.split("_")
    product_id = int(parts[2])
    current_qty = int(parts[3])
    new_qty = current_qty + 1
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        await update_basket_quantity(session, user.id, product_id, new_qty)
        
        basket_items = await get_basket_items(session, user.id)
        
        # Recalculate total
        total = 0
        items_text = ""
        
        for item in basket_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total += item_total
            items_text += f"• {product.name}\n  💰 {format_price(product.price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        text = (
            f"🛒 <b>Mening savatim</b>\n\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(total)} so'm</b>"
        )
        
        keyboard = []
        for item in basket_items:
            keyboard.append([
                InlineKeyboardButton(text="➖", callback_data=f"basket_dec_{item.product_id}_{item.quantity}"),
                InlineKeyboardButton(text=f"{item.product.name}: {item.quantity}", callback_data="basket_display"),
                InlineKeyboardButton(text="➕", callback_data=f"basket_inc_{item.product_id}_{item.quantity}")
            ])
        
        keyboard.append([InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order_prompt")])
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    await callback.answer()


@router.callback_query(F.data.startswith("basket_dec_"))
async def basket_decrease(callback: CallbackQuery):
    from app.database.requests import get_user_by_tg_id
    from app.database.order_requests import update_basket_quantity, get_basket_items
    
    parts = callback.data.split("_")
    product_id = int(parts[2])
    current_qty = int(parts[3])
    new_qty = max(0, current_qty - 1)
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        await update_basket_quantity(session, user.id, product_id, new_qty)
        
        basket_items = await get_basket_items(session, user.id)
        
        if not basket_items:
            await callback.message.edit_text(
                "🛒 <b>Mening savatim</b>\n\n"
                "Savat bo'sh.\n"
                "Buyurtma yaratish uchun mahsulotlarni savatga qo'shing!"
            )
            await callback.answer()
            return
        
        # Recalculate total
        total = 0
        items_text = ""
        
        for item in basket_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total += item_total
            items_text += f"• {product.name}\n  💰 {format_price(product.price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        text = (
            f"🛒 <b>Mening savatim</b>\n\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(total)} so'm</b>"
        )
        
        keyboard = []
        for item in basket_items:
            keyboard.append([
                InlineKeyboardButton(text="➖", callback_data=f"basket_dec_{item.product_id}_{item.quantity}"),
                InlineKeyboardButton(text=f"{item.product.name}: {item.quantity}", callback_data="basket_display"),
                InlineKeyboardButton(text="➕", callback_data=f"basket_inc_{item.product_id}_{item.quantity}")
            ])
        
        keyboard.append([InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order_prompt")])
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    await callback.answer()


@router.callback_query(F.data == "confirm_order_prompt")
async def confirm_order_prompt(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏢 Olish uchun", callback_data="order_pickup"),
                InlineKeyboardButton(text="🚚 Yetkazib berish", callback_data="order_delivery")
            ]
        ]
    )
    
    await callback.message.edit_text(
        "📦 <b>Buyurtmangizni qanday olishni xohlaysiz?</b>\n\n"
        "Yetkazib berish usulini tanlang:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "order_delivery")
async def order_delivery_request_location(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Joylashuv yuborish", callback_data="delivery_location")],
            [InlineKeyboardButton(text="✍️ Manzilni yozish", callback_data="delivery_text")]
        ]
    )
    
    await callback.message.edit_text(
        "📍 <b>Yetkazib berish manzili</b>\n\n"
        "Manzilni qanday ko'rsatishni xohlaysiz?\n\n"
        "• 📍 Joylashuv yuborish - aniq koordinatalar\n"
        "• ✍️ Manzilni yozish - matn ko'rinishida",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "delivery_location")
async def request_location_coords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📍 <b>Joylashuvni yuborish</b>\n\n"
        "Iltimos, yetkazib berish uchun joylashuvingizni yuboring.\n"
        "Joylashuvingizni yuborish uchun 📎 qo'shimcha tugmasidan foydalaning."
    )
    await state.set_state(OrderStates.waiting_for_delivery_location)
    await callback.answer()


@router.callback_query(F.data == "delivery_text")
async def request_text_address(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✍️ <b>Manzilni yozish</b>\n\n"
        "Iltimos, yetkazib berish manzilini matn ko'rinishida yozing.\n\n"
        "Masalan: Toshkent sh., Yunusobod tumani, Amir Temur ko'chasi, 123-uy\n\n"
        "⚠️ Manzil 500 belgidan oshmasligi kerak."
    )
    await state.set_state(OrderStates.waiting_for_text_address)
    await callback.answer()


@router.message(OrderStates.waiting_for_text_address)
async def process_text_address(message: Message, state: FSMContext):
    address = message.text.strip()
    
    if len(address) > 500:
        await message.answer(
            "❌ <b>Manzil juda uzun!</b>\n\n"
            "Iltimos, 500 belgidan kam bo'lgan manzilni kiriting."
        )
        return
    
    if len(address) < 10:
        await message.answer(
            "❌ <b>Manzil juda qisqa!</b>\n\n"
            "Iltimos, to'liq manzilni kiriting."
        )
        return
    
    await state.update_data(
        delivery_type='delivery',
        latitude=None,
        longitude=None,
        address=address
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="confirm_order_yes_delivery"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_order_no")
            ]
        ]
    )
    
    await message.answer(
        f"✍️ <b>Manzil qabul qilindi</b>\n\n"
        f"🏠 Manzil: {address}\n\n"
        f"❓ Buyurtmangizni tasdiqlaysizmi?",
        reply_markup=keyboard
    )


@router.message(OrderStates.waiting_for_delivery_location, F.location)
async def process_delivery_location(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    # Get address from coordinates
    address = get_address_from_coords(latitude, longitude)
    
    await state.update_data(
        delivery_type='delivery',
        latitude=latitude,
        longitude=longitude,
        address=address
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="confirm_order_yes_delivery"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_order_no")
            ]
        ]
    )
    
    await message.answer(
        f"📍 <b>Joylashuv qabul qilindi</b>\n\n"
        f"🏠 Manzil: {address}\n\n"
        f"❓ Buyurtmangizni tasdiqlaysizmi?",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "order_pickup")
async def order_pickup_show_branches(callback: CallbackQuery):
    from app.database.branch_requests import get_all_branches
    
    async with async_session_maker() as session:
        branches = await get_all_branches(session)
    
    if not branches:
        await callback.message.edit_text(
            "🏢 <b>Filiallar mavjud emas</b>\n\n"
            "Afsuski, hozirda olish uchun filiallar mavjud emas.\n"
            "Iltimos, qo'llab-quvvatlash xizmatiga murojaat qiling."
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🏢 <b>Olish uchun filialni tanlang</b>\n\n"
        "Buyurtmangizni olish uchun filialni tanlang:"
    )
    no_desc = "Tavsif yo'q"
    for branch in branches:
        text = (
            f"🏢 <b>{branch.name}</b>\n\n"
            f"📝 {branch.description or no_desc}\n"
            f"📍 Joylashuv: {branch.location}"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📦 Buyurtma berish", callback_data=f"pickup_branch_{branch.id}")]
            ]
        )
        
        if branch.image:
            await callback.message.answer_photo(
                photo=branch.image,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data.startswith("pickup_branch_"))
async def confirm_pickup_branch(callback: CallbackQuery, state: FSMContext):
    branch_id = int(callback.data.split("_")[2])
    
    await state.update_data(
        delivery_type='pickup',
        branch_id=branch_id
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="confirm_order_yes_pickup"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_order_no")
            ]
        ]
    )
    
    await callback.message.answer(
        "❓ <b>Buyurtmani tasdiqlash</b>\n\n"
        "Buyurtmangizni tasdiqlaysizmi?",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_order_no")
async def confirm_order_no(callback: CallbackQuery, state: FSMContext):
    from app.database.requests import get_user_by_tg_id
    from app.database.order_requests import get_basket_items
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        basket_items = await get_basket_items(session, user.id)
        
        # Recalculate total
        total = 0
        items_text = ""
        
        for item in basket_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total += item_total
            items_text += f"• {product.name}\n  💰 {format_price(product.price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        text = (
            f"🛒 <b>Mening savatim</b>\n\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(total)} so'm</b>"
        )
        
        keyboard = []
        for item in basket_items:
            keyboard.append([
                InlineKeyboardButton(text="➖", callback_data=f"basket_dec_{item.product_id}_{item.quantity}"),
                InlineKeyboardButton(text=f"{item.product.name}: {item.quantity}", callback_data="basket_display"),
                InlineKeyboardButton(text="➕", callback_data=f"basket_inc_{item.product_id}_{item.quantity}")
            ])
        
        keyboard.append([InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order_prompt")])
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "confirm_order_yes_delivery")
async def confirm_order_yes_delivery(callback: CallbackQuery, state: FSMContext):
    from app.database.requests import get_user_by_tg_id
    from app.database.order_requests import (
        get_basket_items, 
        create_order, 
        create_order_item, 
        clear_basket
    )
    from app.config import GROUP_ID, BOT_TOKEN
    from aiogram import Bot
    
    bot = Bot(token=BOT_TOKEN)
    data = await state.get_data()
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        basket_items = await get_basket_items(session, user.id)
        
        if not basket_items:
            await callback.answer("Savatingiz bo'sh!", show_alert=True)
            return
        
        # Calculate total
        total = 0
        items_text = ""
        
        for item in basket_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total += item_total
            items_text += f"• {product.name}\n  💰 {format_price(product.price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        # Create order with delivery details
        order = await create_order(
            session, 
            user.id, 
            total,
            delivery_type='delivery',
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            delivery_address=data.get('address')
        )
        
        # Create order items
        for item in basket_items:
            await create_order_item(
                session,
                order.id,
                item.product_id,
                item.product.name,
                float(item.product.price),
                item.quantity
            )
        
        # Send to group with delivery location
        address_info = ""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        text_address = data.get('address')
        
        if text_address:
            address_info = f"🏠 Manzil: {text_address}\n"
        elif latitude and longitude:
            address_info = f"📍 Joylashuv koordinatalari yuborilgan\n"
        
        group_text = (
            f"🆕 <b>Yangi Buyurtma #{order.id}</b>\n\n"
            f"👤 Mijoz: {user.full_name or user.first_name}\n"
            f"📱 Telefon: {user.phone_number or 'Berilmagan'}\n"
            f"🆔 Foydalanuvchi ID: {user.tg_id}\n"
            f"🚚 Yetkazib berish turi: <b>Yetkazib berish</b>\n"
            f"{address_info}\n"
            f"📦 <b>Buyurtma mahsulotlari:</b>\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(total)} so'm</b>\n"
            f"📊 Holati: {order.status}"
        )
        
        group_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"order_status_{order.id}_cancelled"),
                    InlineKeyboardButton(text="✅ Yetkazildi", callback_data=f"order_status_{order.id}_delivered")
                ]
            ]
        )
        
        try:
            # Send text first
            group_message = await bot.send_message(
                chat_id=GROUP_ID,
                text=group_text,
                reply_markup=group_keyboard,
                parse_mode=ParseMode.HTML
            )
            
            # Send location if available
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            if latitude is not None and longitude is not None:
                await bot.send_location(
                    chat_id=GROUP_ID,
                    latitude=latitude,
                    longitude=longitude,
                    reply_to_message_id=group_message.message_id
                )
            
            # Update order with group message id
            order.group_message_id = group_message.message_id
            await session.commit()
        except Exception as e:
            print(f"Error sending to group: {e}")
        
        # Clear basket
        await clear_basket(session, user.id)
    
    await callback.message.edit_text(
        f"✅ <b>Buyurtma tasdiqlandi!</b>\n\n"
        f"Sizning buyurtmangiz #{order.id} muvaffaqiyatli joylashtirildi.\n"
        f"Jami: {format_price(total)} so'm\n"
        f"Yetkazib berish turi: Yetkazib berish\n\n"
        f"Tez orada joylashuvingizga yetkazib beramiz!"
    )
    await state.clear()
    await callback.answer()
    await bot.session.close()


@router.callback_query(F.data == "confirm_order_yes_pickup")
async def confirm_order_yes_pickup(callback: CallbackQuery, state: FSMContext):
    from app.database.requests import get_user_by_tg_id
    from app.database.order_requests import (
        get_basket_items, 
        create_order, 
        create_order_item, 
        clear_basket
    )
    from app.database.branch_requests import get_branch_by_id
    from app.config import GROUP_ID, BOT_TOKEN
    from aiogram import Bot
    
    bot = Bot(token=BOT_TOKEN)
    data = await state.get_data()
    branch_id = data.get('branch_id')
    
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        basket_items = await get_basket_items(session, user.id)
        branch = await get_branch_by_id(session, branch_id)
        
        if not basket_items:
            await callback.answer("Savatingiz bo'sh!", show_alert=True)
            return
        
        # Calculate total
        total = 0
        items_text = ""
        
        for item in basket_items:
            product = item.product
            item_total = float(product.price) * item.quantity
            total += item_total
            items_text += f"• {product.name}\n  💰 {format_price(product.price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        # Create order with pickup details
        order = await create_order(
            session, 
            user.id, 
            total,
            delivery_type='pickup',
            branch_id=branch_id
        )
        
        # Create order items
        for item in basket_items:
            await create_order_item(
                session,
                order.id,
                item.product_id,
                item.product.name,
                float(item.product.price),
                item.quantity
            )
        
        # Send to group with branch info
        group_text = (
            f"🆕 <b>Yangi Buyurtma #{order.id}</b>\n\n"
            f"👤 Mijoz: {user.full_name or user.first_name}\n"
            f"📱 Telefon: {user.phone_number or 'Berilmagan'}\n"
            f"🆔 Foydalanuvchi ID: {user.tg_id}\n"
            f"🏢 Olib ketish filiali: <b>{branch.name}</b>\n"
            f"📍 Filial manzili: {branch.location}\n\n"
            f"📦 <b>Buyurtma mahsulotlari:</b>\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(total)} so'm</b>\n"
            f"📊 Holati: {order.status}"
        )
        
        group_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"order_status_{order.id}_cancelled"),
                    InlineKeyboardButton(text="✅ Yetkazildi", callback_data=f"order_status_{order.id}_delivered")
                ]
            ]
        )
        
        try:
            group_message = await bot.send_message(
                chat_id=GROUP_ID,
                text=group_text,
                reply_markup=group_keyboard,
                parse_mode=ParseMode.HTML
            )
            
            # Update order with group message id
            order.group_message_id = group_message.message_id
            await session.commit()
        except Exception as e:
            print(f"Error sending to group: {e}")
        
        # Clear basket
        await clear_basket(session, user.id)
    
    await callback.message.edit_text(
        f"✅ <b>Buyurtma tasdiqlandi!</b>\n\n"
        f"Mahsulotingiz haqida ma'lumot filialga yuborildi.\n"
        f"Ular tez orada siz bilan bog'lanishadi!\n\n"
        f"📦 Buyurtma #{order.id}\n"
        f"💵 Jami: {format_price(total)} so'm\n"
        f"🏢 Filial: {branch.name}"
    )
    await state.clear()
    await callback.answer()
    await bot.session.close()


@router.callback_query(F.data.startswith("order_status_"))
async def update_order_status_handler(callback: CallbackQuery):
    from app.database.order_requests import update_order_status, get_order_by_id, get_order_items, get_user_by_id
    from app.config import BOT_TOKEN
    from aiogram import Bot
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    new_status = parts[3]
    
    bot = Bot(token=BOT_TOKEN)
    
    async with async_session_maker() as session:
        order = await update_order_status(session, order_id, new_status)
        
        if not order:
            await callback.answer("Buyurtma topilmadi!", show_alert=True)
            return
        
        # Get order details
        order_items = await get_order_items(session, order_id)
        user = await get_user_by_id(session, order.user_id)
        
        items_text = ""
        for item in order_items:
            item_total = float(item.product_price) * item.quantity
            items_text += f"• {item.product_name}\n  💰 {format_price(item.product_price)} so'm x {item.quantity} = {format_price(item_total)} so'm\n\n"
        
        # Get delivery information
        delivery_info = ""
        if order.delivery_type == 'delivery':
            delivery_info = f"🚚 Yetkazib berish turi: <b>Yetkazib berish</b>\n"
            if order.delivery_address:
                delivery_info += f"🏠 Manzil: {order.delivery_address}\n"
            elif order.delivery_latitude and order.delivery_longitude:
                delivery_info += f"📍 Joylashuv koordinatalari yuborilgan\n"
        elif order.delivery_type == 'pickup' and order.branch:
            delivery_info = f"🏢 Olib ketish filiali: <b>{order.branch.name}</b>\n📍 Filial manzili: {order.branch.location}\n"
        
        # Create status message
        status_emoji = "✅" if new_status == "delivered" else "❌"
        status_text = "YETKAZILDI" if new_status == "delivered" else "BEKOR QILINDI"
        
        # Update group message - remove buttons and update text
        updated_group_text = (
            f"🆕 <b>Buyurtma #{order.id}</b>\n\n"
            f"👤 Mijoz: {user.full_name or user.first_name}\n"
            f"📱 Telefon: {user.phone_number or 'Berilmagan'}\n"
            f"🆔 Foydalanuvchi ID: {user.tg_id}\n"
            f"{delivery_info}\n"
            f"📦 <b>Buyurtma mahsulotlari:</b>\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 <b>Jami: {format_price(order.total_price)} so'm</b>\n"
            f"📊 Holati: <b>{status_emoji} {status_text}</b>"
        )
        
        try:
            # Edit message without reply markup to remove buttons
            await callback.message.edit_text(
                updated_group_text, 
                reply_markup=None, 
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error editing group message: {e}")
        
        # Notify user with HTML parse mode
        try:
            user_status_emoji = "✅" if new_status == "delivered" else "❌"
            await bot.send_message(
                chat_id=user.tg_id,
                text=f"{user_status_emoji} <b>Buyurtma #{order.id} holati yangilandi</b>\n\n"
                     f"Buyurtma holati yangilandi: <b>{status_text}</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error notifying user: {e}")
    
    # Show alert notification to admin
    await callback.answer(f"Buyurtma holati yangilandi: {status_text}!", show_alert=True)
    await bot.session.close()
