from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.engine import async_session_maker
from app.database.product_requests import get_products_by_type, get_product_by_id
from app.utils.formatters import format_price

router = Router()


@router.message(F.text == "🥥 Boshqa mahsulotlar")
async def other_products_menu(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Nonushta", callback_data="category_nonushta"),
             InlineKeyboardButton(text="🥤 Detox", callback_data="category_detox")],
            [InlineKeyboardButton(text="🍽 Tushliklar", callback_data="category_tushliklar")],
            [InlineKeyboardButton(text="🍓 FruitMix", callback_data="category_fruitmix"),
             InlineKeyboardButton(text="🌙 Kechki ovqat", callback_data="category_kechki_ovqat")]
        ]
    )
    
    await message.answer(
        "🥥 <b>Boshqa mahsulotlar</b>\n\n"
        "Qo'shimcha mahsulot toifalarini tanlang:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    category_mapping = {
        "category_nonushta": ("Nonushta", "🍳 <b>Nonushta</b>", "Kun boshiga energiya beruvchi mahsulotlar"),
        "category_detox": ("Detox", "🥤 <b>Detox</b>", "Tanani tozalash va detoks qilish uchun mahsulotlar"),
        "category_tushliklar": ("tushliklar", "🍽 <b>Tushliklar</b>", "Kunning o'rtasida energiya beruvchi mahsulotlar"),
        "category_fruitmix": ("FruitMix", "🍓 <b>FruitMix</b>", "Mevali aralashma va vitaminlar"),
        "category_kechki_ovqat": ("kechki ovqat", "🌙 <b>Kechki ovqat</b>", "Kechqurun iste'mol qilish uchun mahsulotlar")
    }
    
    category_data = category_mapping.get(callback.data)
    if not category_data:
        await callback.answer("Noto'g'ri toifa!", show_alert=True)
        return
    
    category_type, title, description = category_data
    
    async with async_session_maker() as session:
        products = await get_products_by_type(session, category_type)
    
    if not products:
        await callback.message.edit_text(
            f"{title}\n\n"
            f"{description}\n\n"
            "Hozircha bu toifada mahsulotlar mavjud emas.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")]]
            )
        )
        await callback.answer()
        return
    
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {format_price(product.price)} so'm",
                callback_data=f"user_product_{product.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")])
    
    await callback.message.edit_text(
        f"{title}\n\n"
        f"{description}\n\n"
        "Batafsil ma'lumot olish uchun mahsulotni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_other_products")
async def back_to_other_products(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Nonushta", callback_data="category_nonushta"),
            InlineKeyboardButton(text="🥤 Detox", callback_data="category_detox")],
            [InlineKeyboardButton(text="🍽 Tushliklar", callback_data="category_tushliklar")],
            [InlineKeyboardButton(text="🍓 FruitMix", callback_data="category_fruitmix"),
            InlineKeyboardButton(text="🌙 Kechki ovqat", callback_data="category_kechki_ovqat")]
        ]
    )
    
    await callback.message.edit_text(
        "🥥 <b>Boshqa mahsulotlar</b>\n\n"
        "Qo'shimcha mahsulot toifalarini tanlang:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_"))
async def back_to_category(callback: CallbackQuery):
    product_type = callback.data.replace("back_to_", "")
    
    async with async_session_maker() as session:
        products = await get_products_by_type(session, product_type)
    
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {format_price(product.price)} so'm",
                callback_data=f"user_product_{product.id}"
            )
        ])
    
    # Determine the category info and back button
    if product_type == "weight_loss":
        title = "🌿 <b>Vazn yo'qotish mahsulotlari</b>\n\n"
        description = "Bu toifadagi mahsulotlar tanangizning ortiqcha vaznini yo'qotishga yordam beradi.\n\n"
    elif product_type == "weight_gain":
        title = "⚖️ <b>Vazn olish mahsulotlari</b>\n\n"
        description = "Bu toifadagi mahsulotlar tanangizga sog'lom vazn va mushak massasini oshirishga yordam beradi.\n\n"
    elif product_type == "Nonushta":
        title = "🍳 <b>Nonushta</b>\n\n"
        description = "Kun boshiga energiya beruvchi mahsulotlar\n\n"
        keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")])
    elif product_type == "Detox":
        title = "🥤 <b>Detox</b>\n\n"
        description = "Tanani tozalash va detoks qilish uchun mahsulotlar\n\n"
        keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")])
    elif product_type == "tushliklar":
        title = "🍽 <b>Tushliklar</b>\n\n"
        description = "Kunning o'rtasida energiya beruvchi mahsulotlar\n\n"
        keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")])
    elif product_type == "FruitMix":
        title = "🍓 <b>FruitMix</b>\n\n"
        description = "Mevali aralashma va vitaminlar\n\n"
        keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")])
    elif product_type == "kechki ovqat":
        title = "🌙 <b>Kechki ovqat</b>\n\n"
        description = "Kechqurun iste'mol qilish uchun mahsulotlar\n\n"
        keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_other_products")])
    else:
        title = f"<b>{product_type}</b>\n\n"
        description = ""
    
    text = title + description + "Batafsil ma'lumot olish uchun mahsulotni tanlang:"
    
    # Check if current message has photo (no text to edit)
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.message(F.text == "🌿 Vazn yo'qotish")
async def lose_weight_menu(message: Message):
    async with async_session_maker() as session:
        products = await get_products_by_type(session, "weight_loss")
    
    if not products:
        await message.answer(
            "🌿 <b>Vazn yo'qotish mahsulotlari</b>\n\n"
            "Bu toifadagi mahsulotlar tanangizning ortiqcha vaznini yo'qotishga yordam beradi.\n\n"
            "Hozircha bu toifada mahsulotlar mavjud emas."
        )
        return
    
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {format_price(product.price)} so'm",
                callback_data=f"user_product_{product.id}"
            )
        ])
    
    await message.answer(
        "🌿 <b>Vazn yo'qotish mahsulotlari</b>\n\n"
        "Tanlab, mahsulot haqida <i>batafsil ma'lumot</i> oling:\n\n"
        "• <b>Protein kokteyllar</b>  \n"
        "• <b>Termogenik suplementlar</b>  \n"
        "• <b>Dietik choylar</b>  \n"
        "• <b>Kaloriya paketlari</b>\n\n"
        "<i>Mahsulotga bosish → batafsil ma'lumot va narx ko‘rsatiladi.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.message(F.text == "⚖️ Vazn olish")
async def gain_weight_menu(message: Message):
    async with async_session_maker() as session:
        products = await get_products_by_type(session, "weight_gain")
    
    if not products:
        await message.answer(
            "⚖️ <b>Vazn olish mahsulotlari</b>\n\n"
            "Bu toifadagi mahsulotlar tanangizga sog'lom vazn va mushak massasini oshirishga yordam beradi.\n\n"
            "Hozircha bu toifada mahsulotlar mavjud emas."
        )
        return
    
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {format_price(product.price)} so'm",
                callback_data=f"user_product_{product.id}"
            )
        ])
    
    await message.answer(
        "⚖️ <b>Vazn olish mahsulotlari</b>\n\n"
        "Tanlab, mahsulot haqida <i>batafsil ma'lumot</i> oling:\n\n"
        "• <b>Protein kokteyllar</b>  \n"
        "• <b>Mass gain paketlari</b>  \n"
        "• <b>Vitamin va minerallar</b>\n\n"
        "<i>Mahsulotga bosish → batafsil ma'lumot va narx ko‘rsatiladi.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("user_product_"))
async def view_user_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    
    async with async_session_maker() as session:
        product = await get_product_by_id(session, product_id)
    
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return
    
    text = (
        f"📦 <b>{product.name}</b>\n\n"
        f"💰 Narxi: {format_price(product.price)} so'm\n"
        f"📝 Tavsif: {product.description or 'Tavsif berilmagan'}\n\n"
        "Bu mahsulotni buyurtma qilish uchun savatga qo'shing!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"add_basket_{product.id}")],
            [InlineKeyboardButton(text="🔙 Mahsulotlarga qaytish", callback_data=f"back_to_{product.type}")]
        ]
    )
    
    if product.product_image:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product.product_image,
            caption=text,
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    await callback.answer()
