import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.engine import async_session_maker
from app.database.requests import get_all_users
from app.keyboards.inline import get_admin_panel_keyboard, get_cancel_keyboard, get_broadcast_confirm_keyboard

router = Router()


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    text = (
        "📢 <b>Barcha foydalanuvchilarga habar yuborish</b>\n\n"
        "Iltimos, yubormoqchi bo'lgan habarni yuboring:\n"
        "• Matn\n"
        "• Rasm\n" 
        "• Video\n"
        "• Hujjat\n"
        "• Stiker va boshqalar"
    )
    
    # Check if current message has photo (no text to edit)
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_cancel_keyboard())
    else:
        await callback.message.edit_text(text, reply_markup=get_cancel_keyboard())
    
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    # Store the entire message data for broadcasting
    message_data = {
        'message_id': message.message_id,
        'chat_id': message.chat.id,
        'content_type': message.content_type,
        'text': message.text,
        'caption': message.caption
    }
    
    # Store media information based on content type
    if message.photo:
        message_data['photo'] = message.photo[-1].file_id
    elif message.video:
        message_data['video'] = message.video.file_id
    elif message.animation:
        message_data['animation'] = message.animation.file_id
    elif message.document:
        message_data['document'] = message.document.file_id
    elif message.audio:
        message_data['audio'] = message.audio.file_id
    elif message.voice:
        message_data['voice'] = message.voice.file_id
    elif message.video_note:
        message_data['video_note'] = message.video_note.file_id
    elif message.sticker:
        message_data['sticker'] = message.sticker.file_id
    elif message.location:
        message_data['location'] = {
            'latitude': message.location.latitude,
            'longitude': message.location.longitude
        }
    elif message.contact:
        message_data['contact'] = {
            'phone_number': message.contact.phone_number,
            'first_name': message.contact.first_name,
            'last_name': message.contact.last_name
        }
    
    await state.update_data(broadcast_message=message_data)
    
    # Get user count for confirmation
    async with async_session_maker() as session:
        users = await get_all_users(session)
    
    # Create preview text based on content type
    content_preview = ""
    if message.text:
        content_preview = f"Matn: <i>{message.text[:100]}{'...' if len(message.text) > 100 else ''}</i>"
    elif message.photo:
        caption_text = f" ({message.caption})" if message.caption else ""
        content_preview = f"Rasm{caption_text}"
    elif message.video:
        caption_text = f" ({message.caption})" if message.caption else ""
        content_preview = f"Video{caption_text}"
    elif message.animation:
        caption_text = f" ({message.caption})" if message.caption else ""
        content_preview = f"GIF{caption_text}"
    elif message.document:
        caption_text = f" ({message.caption})" if message.caption else ""
        content_preview = f"Hujjat{caption_text}"
    elif message.audio:
        caption_text = f" ({message.caption})" if message.caption else ""
        content_preview = f"Audio{caption_text}"
    elif message.voice:
        content_preview = "Ovozli habar"
    elif message.video_note:
        content_preview = "Video habar"
    elif message.sticker:
        content_preview = "Stiker"
    elif message.location:
        content_preview = "Joylashuv"
    elif message.contact:
        content_preview = f"Kontakt: {message.contact.first_name}"
    
    text = (
        f"📢 <b>Habar tasdiqlash</b>\n\n"
        f"Yuborilgan habar:\n"
        f"{content_preview}\n\n"
        f"👥 Habar yuboriladi: <b>{len(users)}</b> ta foydalanuvchiga\n\n"
        f"Habar yuborishni tasdiqlaysizmi?"
    )
    
    await message.answer(text, reply_markup=get_broadcast_confirm_keyboard())
    await state.set_state(BroadcastStates.waiting_for_confirmation)


@router.callback_query(BroadcastStates.waiting_for_confirmation, F.data == "broadcast_confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_data = data['broadcast_message']
    
    # Get all users
    async with async_session_maker() as session:
        users = await get_all_users(session)
    
    if not users:
        await callback.message.edit_text(
            "❌ <b>Foydalanuvchilar topilmadi</b>\n\n"
            "Habar yuborish uchun kamida bitta foydalanuvchi bo'lishi kerak.",
            reply_markup=get_admin_panel_keyboard()
        )
        await state.clear()
        await callback.answer()
        return
    
    # Show sending progress
    content_type = message_data.get('content_type', 'text')
    progress_text = f"📤 <b>Habar yuborilmoqda...</b>\n\nJami foydalanuvchilar: {len(users)}\nTur: {content_type}"
    
    await callback.message.edit_text(progress_text)
    await callback.answer()
    
    # Send message to all users
    successful_sends = 0
    failed_sends = 0
    
    bot = callback.bot
    
    for user in users:
        try:
            # Create admin header
            admin_header = "📢 <b>Admin habari</b>\n\n"
            
            # Send different types of content
            if message_data['content_type'] == 'text':
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=f"{admin_header}{message_data['text']}"
                )
            elif message_data['content_type'] == 'photo':
                caption = message_data.get('caption', '')
                final_caption = f"{admin_header}{caption}" if caption else admin_header.strip()
                await bot.send_photo(
                    chat_id=user.tg_id,
                    photo=message_data['photo'],
                    caption=final_caption
                )
            elif message_data['content_type'] == 'video':
                caption = message_data.get('caption', '')
                final_caption = f"{admin_header}{caption}" if caption else admin_header.strip()
                await bot.send_video(
                    chat_id=user.tg_id,
                    video=message_data['video'],
                    caption=final_caption
                )
            elif message_data['content_type'] == 'animation':
                caption = message_data.get('caption', '')
                final_caption = f"{admin_header}{caption}" if caption else admin_header.strip()
                await bot.send_animation(
                    chat_id=user.tg_id,
                    animation=message_data['animation'],
                    caption=final_caption
                )
            elif message_data['content_type'] == 'document':
                caption = message_data.get('caption', '')
                final_caption = f"{admin_header}{caption}" if caption else admin_header.strip()
                await bot.send_document(
                    chat_id=user.tg_id,
                    document=message_data['document'],
                    caption=final_caption
                )
            elif message_data['content_type'] == 'audio':
                caption = message_data.get('caption', '')
                final_caption = f"{admin_header}{caption}" if caption else admin_header.strip()
                await bot.send_audio(
                    chat_id=user.tg_id,
                    audio=message_data['audio'],
                    caption=final_caption
                )
            elif message_data['content_type'] == 'voice':
                # Send admin header first, then voice
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=admin_header.strip()
                )
                await bot.send_voice(
                    chat_id=user.tg_id,
                    voice=message_data['voice']
                )
            elif message_data['content_type'] == 'video_note':
                # Send admin header first, then video note
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=admin_header.strip()
                )
                await bot.send_video_note(
                    chat_id=user.tg_id,
                    video_note=message_data['video_note']
                )
            elif message_data['content_type'] == 'sticker':
                # Send admin header first, then sticker
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=admin_header.strip()
                )
                await bot.send_sticker(
                    chat_id=user.tg_id,
                    sticker=message_data['sticker']
                )
            elif message_data['content_type'] == 'location':
                # Send admin header first, then location
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=admin_header.strip()
                )
                location = message_data['location']
                await bot.send_location(
                    chat_id=user.tg_id,
                    latitude=location['latitude'],
                    longitude=location['longitude']
                )
            elif message_data['content_type'] == 'contact':
                # Send admin header first, then contact
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=admin_header.strip()
                )
                contact = message_data['contact']
                await bot.send_contact(
                    chat_id=user.tg_id,
                    phone_number=contact['phone_number'],
                    first_name=contact['first_name'],
                    last_name=contact.get('last_name')
                )
            
            successful_sends += 1
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.05)
            
        except Exception as e:
            failed_sends += 1
            logging.warning(f"Failed to send message to user {user.tg_id}: {e}")
    
    # Show results
    result_text = (
        f"✅ <b>Habar yuborish yakunlandi!</b>\n\n"
        f"📊 Natija:\n"
        f"• Muvaffaqiyatli yuborildi: {successful_sends}\n"
        f"• Xatolik yuz berdi: {failed_sends}\n"
        f"• Jami: {len(users)}"
    )
    
    await callback.message.edit_text(result_text, reply_markup=get_admin_panel_keyboard())
    await state.clear()


@router.callback_query(BroadcastStates.waiting_for_confirmation, F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "❌ <b>Habar yuborish bekor qilindi</b>",
        reply_markup=get_admin_panel_keyboard()
    )
    await state.clear()
    await callback.answer()