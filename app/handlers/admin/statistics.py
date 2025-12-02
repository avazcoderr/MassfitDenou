from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from app.database.engine import async_session_maker
from app.database.requests import (
    get_total_users_count, get_weekly_users_stats, get_monthly_users_stats,
    get_daily_revenue, get_weekly_revenue, get_monthly_revenue,
    get_daily_cancelled_orders, get_weekly_cancelled_orders, get_monthly_cancelled_orders
)
from app.keyboards.inline import (
    get_user_stats_keyboard, get_revenue_stats_keyboard, 
    get_cancelled_orders_stats_keyboard, get_admin_panel_keyboard
)
from app.utils.formatters import format_price
from app.config import is_admin

router = Router()


@router.callback_query(F.data == "user_stats")
async def show_user_stats_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👥 <b>User statistikasi</b>\n\n"
        "Kerakli statistika turini tanlang:",
        reply_markup=get_user_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "all_users_stats")
async def show_all_users_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        total_users = await get_total_users_count(session)
    
    text = (
        f"👥 <b>Barcha foydalanuvchilar</b>\n\n"
        f"📊 Jami foydalanuvchilar soni: <b>{total_users}</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_user_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "weekly_users_stats")
async def show_weekly_users_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        weekly_stats = await get_weekly_users_stats(session)
    
    text = (
        f"📅 <b>Haftalik foydalanuvchilar statistikasi</b>\n\n"
        f"🆕 Bu hafta qo'shilganlar: <b>{weekly_stats['new_users_this_week']}</b>\n"
        f"👥 Bir hafta oldin mavjud bo'lganlar: <b>{weekly_stats['users_week_ago']}</b>\n"
        f"📊 Jami: <b>{weekly_stats['new_users_this_week'] + weekly_stats['users_week_ago']}</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_user_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "monthly_users_stats")
async def show_monthly_users_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        monthly_stats = await get_monthly_users_stats(session)
    
    text = (
        f"📆 <b>Oylik foydalanuvchilar statistikasi</b>\n\n"
        f"🆕 Bu oy qo'shilganlar: <b>{monthly_stats['new_users_this_month']}</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_user_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "revenue_stats")
async def show_revenue_stats_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💰 <b>Daromad statistikasi</b>\n\n"
        "Kerakli davr statistikasini tanlang:\n\n"
        "⚠️ <i>Faqat yetkazilgan buyurtmalar hisobga olinadi</i>",
        reply_markup=get_revenue_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "daily_revenue_stats")
async def show_daily_revenue_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        daily_revenue = await get_daily_revenue(session)
    
    text = (
        f"📅 <b>1 kunlik daromad</b>\n\n"
        f"💵 So'nggi 24 soat davridagi daromad: <b>{format_price(daily_revenue)} so'm</b>\n\n"
        f"⚠️ <i>Faqat yetkazilgan buyurtmalar hisobga olingan</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_revenue_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "weekly_revenue_stats")
async def show_weekly_revenue_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        weekly_revenue = await get_weekly_revenue(session)
    
    text = (
        f"📊 <b>1 haftalik daromad</b>\n\n"
        f"💵 So'nggi 7 kun davridagi daromad: <b>{format_price(weekly_revenue)} so'm</b>\n\n"
        f"⚠️ <i>Faqat yetkazilgan buyurtmalar hisobga olingan</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_revenue_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "monthly_revenue_stats")
async def show_monthly_revenue_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        monthly_revenue = await get_monthly_revenue(session)
    
    text = (
        f"📈 <b>1 oylik daromad</b>\n\n"
        f"💵 Joriy oy boshidan bugungi kungacha daromad: <b>{format_price(monthly_revenue)} so'm</b>\n\n"
        f"⚠️ <i>Faqat yetkazilgan buyurtmalar hisobga olingan</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_revenue_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "cancelled_orders_stats")
async def show_cancelled_orders_stats_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "❌ <b>Bekor qilingan buyurtmalar statistikasi</b>\n\n"
        "Kerakli davr statistikasini tanlang:",
        reply_markup=get_cancelled_orders_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "daily_cancelled_stats")
async def show_daily_cancelled_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        cancelled_stats = await get_daily_cancelled_orders(session)
    
    text = (
        f"📅 <b>1 kunlik bekor qilingan buyurtmalar</b>\n\n"
        f"❌ So'nggi 24 soat davomida bekor qilingan: <b>{cancelled_stats['count']}</b> ta buyurtma\n"
        f"💸 Bekor qilingan buyurtmalar umumiy qiymati: <b>{format_price(cancelled_stats['revenue'])} so'm</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancelled_orders_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "weekly_cancelled_stats")
async def show_weekly_cancelled_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        cancelled_stats = await get_weekly_cancelled_orders(session)
    
    text = (
        f"📊 <b>1 haftalik bekor qilingan buyurtmalar</b>\n\n"
        f"❌ So'nggi 7 kun davomida bekor qilingan: <b>{cancelled_stats['count']}</b> ta buyurtma\n"
        f"💸 Bekor qilingan buyurtmalar umumiy qiymati: <b>{format_price(cancelled_stats['revenue'])} so'm</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancelled_orders_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "monthly_cancelled_stats")
async def show_monthly_cancelled_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Sizda bu amalni bajarish huquqi yo'q.", show_alert=True)
        return
    
    async with async_session_maker() as session:
        cancelled_stats = await get_monthly_cancelled_orders(session)
    
    text = (
        f"📈 <b>1 oylik bekor qilingan buyurtmalar</b>\n\n"
        f"❌ Joriy oy boshidan bugungi kungacha bekor qilingan: <b>{cancelled_stats['count']}</b> ta buyurtma\n"
        f"💸 Bekor qilingan buyurtmalar umumiy qiymati: <b>{format_price(cancelled_stats['revenue'])} so'm</b>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancelled_orders_stats_keyboard()
    )
    await callback.answer()