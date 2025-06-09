# Enhanced Telegram Bot with Statistics and Admin Panel - Version 1.2 (Fixed f-string syntax)
import os
import json
import logging
from typing import Dict, Optional, List
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from datetime import datetime, date
import platform
import psutil

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Bot token and admin ID from environment variables
BOT_TOKEN = os.getenv("8037505019:AAGY0g3ZrWtgV1A7VSb5M0JD8wm471RRTeI")
ADMIN_ID = int(os.getenv("5660670674", "0"))  # Convert to int, default to 0 if not set

# Initialize bot and dispatcher
bot = Bot(token="8037505019:AAGY0g3ZrWtgV1A7VSb5M0JD8wm471RRTeI")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States for admin actions
class AdminStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_video = State()
    waiting_for_ad = State()
    waiting_for_channel = State()
    waiting_for_delete_code = State()
    waiting_for_add_admin = State()  # New state for adding admin
    waiting_for_delete_admin = State()  # New state for deleting admin

# Helper functions
def load_videos() -> Dict:
    try:
        with open('videos.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"mappings": {}}

def save_videos(data: Dict):
    with open('videos.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_users() -> list:
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)["users"]
    except FileNotFoundError:
        return []

def save_user(user_id: int):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=4)

def load_admins() -> list:
    try:
        with open('admins.json', 'r', encoding='utf-8') as f:
            return json.load(f)["admins"]
    except FileNotFoundError:
        return [5660670674]  # Default admin

def save_admin(admin_id: int):
    admins = load_admins()
    if admin_id not in admins:
        admins.append(admin_id)
        with open('admins.json', 'w', encoding='utf-8') as f:
            json.dump({"admins": admins}, f, ensure_ascii=False, indent=4)

def delete_admin(admin_id: int):
    admins = load_admins()
    if admin_id in admins and admin_id != 5660670674:  # Don't delete main admin
        admins.remove(admin_id)
        with open('admins.json', 'w', encoding='utf-8') as f:
            json.dump({"admins": admins}, f, ensure_ascii=False, indent=4)

def is_admin(user_id: int) -> bool:
    admins = load_admins()
    return user_id in admins

def load_channels() -> List[Dict]:
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            return json.load(f)["channels"]
    except FileNotFoundError:
        return []

def save_channel(channel_id: str, channel_name: str, invite_link: str):
    channels = load_channels()
    # Check if channel already exists
    if not any(ch["id"] == channel_id for ch in channels):
        channels.append({
            "id": channel_id,
            "name": channel_name,
            "invite_link": invite_link
        })
        with open('channels.json', 'w', encoding='utf-8') as f:
            json.dump({"channels": channels}, f, ensure_ascii=False, indent=4)

def delete_channel(channel_id: str):
    channels = load_channels()
    channels = [ch for ch in channels if ch["id"] != channel_id]
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump({"channels": channels}, f, ensure_ascii=False, indent=4)

async def check_subscription(user_id: int) -> bool:
    channels = load_channels()
    if not channels:  # If no channels are set, consider user as subscribed
        return True
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel["id"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logging.error(f"Error checking subscription for {user_id} in {channel['id']}: {e}")
            return False
    return True

# Helper functions for enhanced statistics
def load_stats() -> Dict:
    try:
        with open('stats.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "daily_stats": {},
            "code_usage": {},
            "user_activity": {},
            "monthly_stats": {}
        }

def save_stats(data: Dict):
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_daily_stats():
    stats = load_stats()
    today = date.today().isoformat()
    
    if today not in stats["daily_stats"]:
        stats["daily_stats"][today] = {
            "users": 0,
            "codes_used": 0,
            "new_users": 0
        }
    
    # Don't save here, just ensure structure exists
    return stats

def update_code_usage(code: str):
    stats = load_stats()
    
    if code not in stats["code_usage"]:
        stats["code_usage"][code] = 0
    
    stats["code_usage"][code] += 1
    save_stats(stats)

def update_user_activity(user_id: int):
    stats = load_stats()
    today = date.today().isoformat()
    
    if str(user_id) not in stats["user_activity"]:
        stats["user_activity"][str(user_id)] = {
            "first_seen": today,
            "last_seen": today,
            "total_usage": 0,
            "daily_usage": {}
        }
    
    user_data = stats["user_activity"][str(user_id)]
    user_data["last_seen"] = today
    user_data["total_usage"] += 1
    
    if today not in user_data["daily_usage"]:
        user_data["daily_usage"][today] = 0
    
    user_data["daily_usage"][today] += 1
    save_stats(stats)

def update_monthly_stats():
    stats = load_stats()
    current_month = datetime.now().strftime("%Y-%m")
    
    if current_month not in stats["monthly_stats"]:
        stats["monthly_stats"][current_month] = {
            "total_users": 0,
            "total_codes_used": 0,
            "new_users": 0
        }
    
    # Don't save here, just ensure structure exists
    return stats

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Check if this is a new user BEFORE saving
    users = load_users()
    is_new_user = message.from_user.id not in users
    
    # Save user when they start the bot
    save_user(message.from_user.id)
    
    # Update statistics for new user
    stats = update_daily_stats()
    monthly_stats = update_monthly_stats()
    today = date.today().isoformat()
    current_month = datetime.now().strftime("%Y-%m")
    
    # Update statistics if this is a new user
    if is_new_user:
        stats["daily_stats"][today]["new_users"] += 1
        monthly_stats["monthly_stats"][current_month]["new_users"] += 1
        save_stats(stats)
        save_stats(monthly_stats)
    
    # Check subscription
    if not await check_subscription(message.from_user.id):
        channels = load_channels()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ch["name"], url=ch["invite_link"])]
            for ch in channels
        ] + [[InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_sub")]])
        
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak:",
            reply_markup=keyboard
        )
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Yordam", callback_data="help")]
    ])
    await message.answer(
        "👋 Salom! Men video kodlarini qayta ishlash uchun yaratilgan botman.\n\n"
        "Video olish uchun kodni matn ko'rinishida yuboring.",
        reply_markup=keyboard
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi kod qo'shish", callback_data="add_code")],
        [InlineKeyboardButton(text="🗑 Kod o'chirish", callback_data="delete_code")],
        [InlineKeyboardButton(text="📋 Kodlar ro'yxati", callback_data="list_codes")],
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="send_ad")],
        [InlineKeyboardButton(text="📢 Kanal boshqaruvi", callback_data="manage_channels")],
        [InlineKeyboardButton(text="👥 Admin boshqaruvi", callback_data="manage_admins")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="show_stats")]  # New button
    ])
    await message.answer("🔐 Admin panel:", reply_markup=keyboard)

# Callback query handlers
@dp.callback_query(F.data == "help")
async def process_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📝 Botdan foydalanish bo'yicha yo'riqnoma:\n\n"
        "1. Video olish uchun kodni matn ko'rinishida yuboring\n"
        "2. Agar kod to'g'ri bo'lsa, video avtomatik ravishda yuboriladi\n"
        "3. Agar kod noto'g'ri bo'lsa, xabar qaytariladi\n\n"
        "Admin uchun:\n"
        "/admin - Admin panelni ochish"
    )

@dp.callback_query(F.data == "add_code")
async def process_add_code(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Yangi kodni kiriting:")
    await state.set_state(AdminStates.waiting_for_code)

@dp.callback_query(F.data == "delete_code")
async def process_delete_code(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    videos = load_videos()
    if not videos["mappings"]:
        await callback.message.edit_text(
            "📭 Kodlar ro'yxati bo'sh!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
            ])
        )
        return
    
    # Show available codes and ask for input
    codes_list = "\n".join([f"• {code}" for code in videos["mappings"].keys()])
    await callback.message.edit_text(
        f"🗑 Kod o'chirish uchun kodni kiriting:\n\n"
        f"Mavjud kodlar:\n{codes_list}\n\n"
        f"O'chirish uchun kodni matn ko'rinishida yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ])
    )
    await state.set_state(AdminStates.waiting_for_delete_code)

@dp.message(AdminStates.waiting_for_delete_code)
async def process_delete_code_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    code = message.text.strip()
    videos = load_videos()
    
    if code in videos["mappings"]:
        # Delete the file
        file_path = videos["mappings"][code]
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
        
        # Remove from mappings
        del videos["mappings"][code]
        save_videos(videos)
        
        await message.answer(
            f"✅ '{code}' kodi muvaffaqiyatli o'chirildi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
            ])
        )
    else:
        await message.answer(
            f"❌ '{code}' kodi topilmadi! Iltimos, mavjud kodlardan birini kiriting.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
            ])
        )
    
    await state.clear()

@dp.callback_query(F.data == "list_codes")
async def process_list_codes(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    videos = load_videos()
    if not videos["mappings"]:
        await callback.message.edit_text("📭 Kodlar ro'yxati bo'sh!")
        return
    
    codes_list = "\n".join([f"• {code}" for code in videos["mappings"].keys()])
    await callback.message.edit_text(f"📋 Mavjud kodlar:\n\n{codes_list}")

@dp.callback_query(F.data == "send_ad")
async def process_send_ad(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 Reklama yuborish uchun quyidagi formatlardan birini tanlang:\n\n"
        "1. Oddiy matn\n"
        "2. Rasm + matn\n"
        "3. Video + matn\n"
        "4. Hujjat + matn\n\n"
        "Avval reklama turini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Oddiy matn", callback_data="ad_text")],
            [InlineKeyboardButton(text="🖼 Rasm + matn", callback_data="ad_photo")],
            [InlineKeyboardButton(text="🎥 Video + matn", callback_data="ad_video")],
            [InlineKeyboardButton(text="📄 Hujjat + matn", callback_data="ad_document")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ])
    )

@dp.callback_query(F.data == "back_to_admin")
async def process_back_to_admin(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi kod qo'shish", callback_data="add_code")],
        [InlineKeyboardButton(text="🗑 Kod o'chirish", callback_data="delete_code")],
        [InlineKeyboardButton(text="📋 Kodlar ro'yxati", callback_data="list_codes")],
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="send_ad")],
        [InlineKeyboardButton(text="📢 Kanal boshqaruvi", callback_data="manage_channels")],
        [InlineKeyboardButton(text="👥 Admin boshqaruvi", callback_data="manage_admins")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="show_stats")]  # New button
    ])
    await callback.message.edit_text("🔐 Admin panel:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("ad_"))
async def process_ad_type(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    ad_type = callback.data[3:]  # Remove "ad_" prefix
    await state.update_data(ad_type=ad_type)
    
    if ad_type == "text":
        await callback.message.edit_text(
            "📝 Reklama matnini kiriting:\n\n"
            "⚠️ Eslatma: Reklama barcha foydalanuvchilarga yuboriladi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="send_ad")]
            ])
        )
    else:
        await callback.message.edit_text(
            f"📤 Reklama uchun {'rasm' if ad_type == 'photo' else 'video' if ad_type == 'video' else 'hujjat'} yuboring:\n\n"
            "⚠️ Eslatma: Reklama barcha foydalanuvchilarga yuboriladi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="send_ad")]
            ])
        )
    
    await state.set_state(AdminStates.waiting_for_ad)

@dp.message(AdminStates.waiting_for_ad)
async def process_ad_content(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    data = await state.get_data()
    ad_type = data["ad_type"]
    
    # Get all users from the database
    users = load_users()
    sent_count = 0
    failed_count = 0
    
    if ad_type == "text":
        # Send text advertisement
        for user_id in users:
            try:
                await bot.send_message(
                    user_id,
                    f"📢 Reklama:\n\n{message.text}",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    elif ad_type == "photo" and message.photo:
        # Send photo advertisement
        for user_id in users:
            try:
                await bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption or "📢 Reklama",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    elif ad_type == "video" and message.video:
        # Send video advertisement
        for user_id in users:
            try:
                await bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption or "📢 Reklama",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    elif ad_type == "document" and message.document:
        # Send document advertisement
        for user_id in users:
            try:
                await bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption or "📢 Reklama",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    else:
        await message.answer(
            "❌ Noto'g'ri format! Iltimos, qaytadan urinib ko'ring.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="send_ad")]
            ])
        )
        return
    
    await state.clear()

# State handlers - these will be processed before the universal handler
@dp.message(AdminStates.waiting_for_code)
async def process_code_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    code = message.text.strip()
    videos = load_videos()
    
    if code in videos["mappings"]:
        await message.answer("❌ Bu kod allaqachon mavjud! Boshqa kod kiriting:")
        return
    
    await state.update_data(code=code)
    await message.answer("📤 Endi faylni yuboring (video, rasm, audio, hujjat va boshqalar):")
    await state.set_state(AdminStates.waiting_for_video)

@dp.message(AdminStates.waiting_for_video, F.content_type.in_({"video", "photo", "document", "audio", "voice", "video_note"}))
async def process_file_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    data = await state.get_data()
    code = data["code"]
    
    # Get file based on content type
    if message.content_type == "video":
        file = message.video
        file_extension = ".mp4"
    elif message.content_type == "photo":
        file = message.photo[-1]  # Get the highest quality photo
        file_extension = ".jpg"
    elif message.content_type == "document":
        file = message.document
        file_extension = os.path.splitext(file.file_name)[1] if file.file_name else ".bin"
    elif message.content_type == "audio":
        file = message.audio
        file_extension = ".mp3"
    elif message.content_type == "voice":
        file = message.voice
        file_extension = ".ogg"
    elif message.content_type == "video_note":
        file = message.video_note
        file_extension = ".mp4"
    
    # Save file
    file_path = f"videos/{code}{file_extension}"
    os.makedirs("videos", exist_ok=True)
    await bot.download(file, destination=file_path)
    
    # Update mappings
    videos = load_videos()
    videos["mappings"][code] = file_path
    save_videos(videos)
    
    await message.answer(f"✅ '{code}' kodi uchun fayl muvaffaqiyatli qo'shildi!")
    await state.clear()

@dp.message(AdminStates.waiting_for_video)
async def process_invalid_file(message: types.Message):
    await message.answer("❌ Iltimos, fayl yuboring (video, rasm, audio, hujjat va boshqalar)!")

@dp.message(AdminStates.waiting_for_ad)
async def process_ad_content(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    data = await state.get_data()
    ad_type = data["ad_type"]
    
    # Get all users from the database
    users = load_users()
    sent_count = 0
    failed_count = 0
    
    if ad_type == "text":
        # Send text advertisement
        for user_id in users:
            try:
                await bot.send_message(
                    user_id,
                    f"📢 Reklama:\n\n{message.text}",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    elif ad_type == "photo" and message.photo:
        # Send photo advertisement
        for user_id in users:
            try:
                await bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption or "📢 Reklama",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    elif ad_type == "video" and message.video:
        # Send video advertisement
        for user_id in users:
            try:
                await bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption or "📢 Reklama",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    elif ad_type == "document" and message.document:
        # Send document advertisement
        for user_id in users:
            try:
                await bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption or "📢 Reklama",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send ad to {user_id}: {e}")
                failed_count += 1
        
        await message.answer(
            f"✅ Reklama yuborildi!\n\n"
            f"📊 Statistika:\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {failed_count}"
        )
    
    else:
        await message.answer(
            "❌ Noto'g'ri format! Iltimos, qaytadan urinib ko'ring.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="send_ad")]
            ])
        )
        return
    
    await state.clear()

@dp.message(AdminStates.waiting_for_channel)
async def process_channel_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    try:
        # Parse channel information
        lines = message.text.strip().split('\n')
        channel_info = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                channel_info[key.strip().lower()] = value.strip()
        
        if not all(k in channel_info for k in ['kanal username', 'kanal nomi', 'invite link']):
            raise ValueError("Noto'g'ri format")
        
        channel_id = channel_info['kanal username']
        channel_name = channel_info['kanal nomi']
        invite_link = channel_info['invite link']
        
        # Verify bot is admin in the channel
        try:
            bot_member = await bot.get_chat_member(channel_id, bot.id)
            if bot_member.status not in ["administrator", "creator"]:
                await message.answer(
                    "❌ Bot kanalda admin emas! Iltimos, botni kanalga admin qiling.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
                    ])
                )
                return
        except Exception as e:
            await message.answer(
                "❌ Kanal topilmadi yoki bot kanalga qo'shilmagan!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
                ])
            )
            return
        
        # Save channel
        save_channel(channel_id, channel_name, invite_link)
        await message.answer(
            f"✅ Kanal muvaffaqiyatli qo'shildi!\n\n"
            f"📢 Kanal: {channel_name}\n"
            f"🔗 Link: {invite_link}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
            ])
        )
    except Exception as e:
        await message.answer(
            "❌ Noto'g'ri format! Iltimos, ko'rsatilgan formatda yuboring:\n\n"
            "Kanal username: @channel_username\n"
            "Kanal nomi: Kanal nomi\n"
            "Invite link: https://t.me/channel_username",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
            ])
        )
    
    await state.clear()

@dp.message(AdminStates.waiting_for_delete_code)
async def process_delete_code_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    code = message.text.strip()
    videos = load_videos()
    
    if code in videos["mappings"]:
        # Delete the file
        file_path = videos["mappings"][code]
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
        
        # Remove from mappings
        del videos["mappings"][code]
        save_videos(videos)
        
        await message.answer(
            f"✅ '{code}' kodi muvaffaqiyatli o'chirildi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
            ])
        )
    else:
        await message.answer(
            f"❌ '{code}' kodi topilmadi! Iltimos, mavjud kodlardan birini kiriting.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
            ])
        )
    
    await state.clear()

@dp.message(AdminStates.waiting_for_add_admin)
async def process_add_admin_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    try:
        admin_id = int(message.text.strip())
        
        # Check if user exists
        try:
            user = await bot.get_chat(admin_id)
            if user.type != "private":
                await message.answer(
                    "❌ Bu ID guruh yoki kanal ID raqami! Faqat foydalanuvchi ID raqamini kiriting.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
                    ])
                )
                return
        except Exception as e:
            await message.answer(
                "❌ Foydalanuvchi topilmadi! Iltimos, to'g'ri Telegram ID raqamini kiriting.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
                ])
            )
            return
        
        # Save admin
        save_admin(admin_id)
        await message.answer(
            f"✅ Yangi admin muvaffaqiyatli qo'shildi!\n\n"
            f"👤 Foydalanuvchi: {user.first_name}\n"
            f"🆔 ID: {admin_id}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
            ])
        )
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format! Iltimos, faqat raqam kiriting.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
            ])
        )
    
    await state.clear()

@dp.message(AdminStates.waiting_for_delete_admin)
async def process_delete_admin_input(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        await state.clear()
        return
    
    try:
        admin_id = int(message.text.strip())
        admins = load_admins()
        
        if admin_id == 5660670674:
            await message.answer(
                "❌ Asosiy admin o'chirilmaydi!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
                ])
            )
            await state.clear()
            return
        
        if admin_id in admins:
            # Get user info before deleting
            try:
                user = await bot.get_chat(admin_id)
                user_name = user.first_name
            except:
                user_name = "Noma'lum"
            
            # Delete admin
            delete_admin(admin_id)
            await message.answer(
                f"✅ Admin muvaffaqiyatli o'chirildi!\n\n"
                f"👤 Foydalanuvchi: {user_name}\n"
                f"🆔 ID: {admin_id}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
                ])
            )
        else:
            await message.answer(
                f"❌ {admin_id} ID raqamiga ega admin topilmadi!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
                ])
            )
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format! Iltimos, faqat raqam kiriting.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
            ])
        )
    
    await state.clear()

@dp.callback_query(F.data == "list_admins")
async def process_list_admins(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    admins = load_admins()
    if not admins:
        await callback.message.edit_text(
            "📭 Adminlar ro'yxati bo'sh!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
            ])
        )
        return
    
    admins_list = []
    for admin_id in admins:
        try:
            user = await bot.get_chat(admin_id)
            status = "👑 Asosiy admin" if admin_id == 5660670674 else "👤 Admin"
            admins_list.append(f"{status}: {user.first_name} ({admin_id})")
        except:
            admins_list.append(f"👤 Admin: Noma'lum ({admin_id})")
    
    admins_text = "\n".join(admins_list)
    
    await callback.message.edit_text(
        f"📋 Mavjud adminlar:\n\n{admins_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
        ])
    )

@dp.callback_query(F.data == "show_stats")
async def process_show_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    # Load data
    videos = load_videos()
    users = load_users()
    channels = load_channels()
    admins = load_admins()
    stats = load_stats()
    
    # Calculate basic statistics
    total_codes = len(videos["mappings"])
    total_users = len(users)
    total_channels = len(channels)
    total_admins = len(admins)
    
    # Calculate file types
    file_types = {}
    for file_path in videos["mappings"].values():
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            file_types['rasm'] = file_types.get('rasm', 0) + 1
        elif ext in ['.mp4', '.avi', '.mov']:
            file_types['video'] = file_types.get('video', 0) + 1
        elif ext in ['.mp3', '.ogg', '.wav']:
            file_types['audio'] = file_types.get('audio', 0) + 1
        elif ext in ['.doc', '.docx', '.pdf', '.txt']:
            file_types['hujjat'] = file_types.get('hujjat', 0) + 1
        else:
            file_types['boshqa'] = file_types.get('boshqa', 0) + 1
    
    # Calculate total file size
    total_size = 0
    for file_path in videos["mappings"].values():
        try:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
        except:
            pass
    
    # Convert to MB
    total_size_mb = total_size / (1024 * 1024)
    
    # Enhanced statistics
    today = date.today().isoformat()
    current_month = datetime.now().strftime("%Y-%m")
    
    # Daily stats
    daily_stats = stats["daily_stats"].get(today, {})
    today_users = daily_stats.get("users", 0)
    today_codes = daily_stats.get("codes_used", 0)
    today_new_users = daily_stats.get("new_users", 0)
    
    # Monthly stats
    monthly_stats = stats["monthly_stats"].get(current_month, {})
    month_users = monthly_stats.get("total_users", 0)
    month_codes = monthly_stats.get("total_codes_used", 0)
    month_new_users = monthly_stats.get("new_users", 0)
    
    # Top codes
    code_usage = stats["code_usage"]
    top_codes = sorted(code_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Count active users (users who used the bot)
    user_activity = stats["user_activity"]
    active_users_count = len(user_activity)
    
    # Create enhanced statistics message
    stats_text = f"""
📊 Kengaytirilgan statistika:

👥 Foydalanuvchilar:
• Jami foydalanuvchilar: {total_users}
• Faol foydalanuvchilar: {active_users_count}
• Bugun faol: {today_users}
• Bugun yangi: {today_new_users}
• Bu oy yangi: {month_new_users}

🔐 Adminlar:
• Jami adminlar: {total_admins}

📁 Fayllar:
• Jami kodlar: {total_codes}
• Jami hajm: {total_size_mb:.2f} MB

📂 Fayl turlari:
"""
    
    for file_type, count in file_types.items():
        stats_text += f"• {file_type.title()}: {count}\n"
    
    if top_codes:
        stats_text += f"""
🔥 Eng ko'p ishlatilgan kodlar:
"""
        
        for i, (code, usage) in enumerate(top_codes, 1):
            stats_text += f"• {i}. {code}: {usage} marta\n"
    else:
        stats_text += "\n🔥 Eng ko'p ishlatilgan kodlar: Hali ma'lumot yo'q\n"
    
    stats_text += f"""
📅 Bugungi faollik:
• Kodlar ishlatildi: {today_codes}
• Yangi foydalanuvchilar: {today_new_users}

📈 Bu oy statistikasi:
• Jami kodlar: {month_codes}
• Yangi foydalanuvchilar: {month_new_users}

📢 Kanallar:
• Obuna kanallari: {total_channels}

🔄 Faol kanallar:
"""
    
    active_channels = 0
    for channel in channels:
        try:
            chat = await bot.get_chat(channel["id"])
            member_count = await bot.get_chat_member_count(channel["id"])
            stats_text += f"• {channel['name']}: {member_count} obunachi\n"
            active_channels += 1
        except:
            stats_text += f"• {channel['name']}: ❌ Xatolik\n"
    
    stats_text += f"\n✅ Faol kanallar: {active_channels}/{total_channels}"
    
    # System info
    stats_text += f"""

💻 Tizim ma'lumotlari:
• OS: {platform.system()} {platform.release()}
• Python: {platform.python_version()}
• CPU: {psutil.cpu_percent()}%
• RAM: {psutil.virtual_memory().percent}%
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="show_stats")],
        [InlineKeyboardButton(text="📥 Foydalanuvchilar ro'yxati", callback_data="export_users")],
        [InlineKeyboardButton(text="📊 Batafsil statistika", callback_data="detailed_stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)

@dp.callback_query(F.data == "detailed_stats")
async def process_detailed_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    stats = load_stats()
    
    # Get last 7 days stats
    from datetime import timedelta
    last_7_days = []
    for i in range(7):
        day = date.today() - timedelta(days=i)
        last_7_days.append(day.isoformat())
    
    detailed_text = "📊 Batafsil statistika (so'nggi 7 kun):\n\n"
    
    for day in reversed(last_7_days):
        day_stats = stats["daily_stats"].get(day, {})
        users = day_stats.get("users", 0)
        codes = day_stats.get("codes_used", 0)
        new_users = day_stats.get("new_users", 0)
        
        detailed_text += f"📅 {day}:\n"
        detailed_text += f"• Faol foydalanuvchilar: {users}\n"
        detailed_text += f"• Kodlar ishlatildi: {codes}\n"
        detailed_text += f"• Yangi foydalanuvchilar: {new_users}\n\n"
    
    # Monthly comparison
    current_month = datetime.now().strftime("%Y-%m")
    last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    
    current_month_stats = stats["monthly_stats"].get(current_month, {})
    last_month_stats = stats["monthly_stats"].get(last_month, {})
    
    detailed_text += f"📈 Oylik taqqoslash:\n"
    detailed_text += f"Bu oy: {current_month_stats.get('total_codes_used', 0)} kod\n"
    detailed_text += f"O'tgan oy: {last_month_stats.get('total_codes_used', 0)} kod\n\n"
    
    # Code usage statistics
    code_usage = stats["code_usage"]
    if code_usage:
        detailed_text += "📊 Kod ishlatish statistikasi:\n"
        total_usage = sum(code_usage.values())
        detailed_text += f"• Jami ishlatilgan: {total_usage} marta\n"
        detailed_text += f"• O'rtacha har bir kod: {total_usage / len(code_usage):.1f} marta\n\n"
        
        # Most and least used codes
        most_used = max(code_usage.items(), key=lambda x: x[1])
        least_used = min(code_usage.items(), key=lambda x: x[1])
        detailed_text += f"🔥 Eng ko'p ishlatilgan: {most_used[0]} ({most_used[1]} marta)\n"
        detailed_text += f"❄️ Eng kam ishlatilgan: {least_used[0]} ({least_used[1]} marta)\n\n"
    
    # User activity statistics
    user_activity = stats["user_activity"]
    if user_activity:
        detailed_text += "👥 Foydalanuvchi faolligi:\n"
        total_activity = sum(user["total_usage"] for user in user_activity.values())
        detailed_text += f"• Jami faol foydalanuvchilar: {len(user_activity)}\n"
        detailed_text += f"• Jami faollik: {total_activity} marta\n"
        detailed_text += f"• O'rtacha har bir foydalanuvchi: {total_activity / len(user_activity):.1f} marta\n\n"
        
        # Most active user count
        most_active_usage = max(user["total_usage"] for user in user_activity.values())
        detailed_text += f"👑 Eng faol foydalanuvchi: {most_active_usage} marta ishlatgan\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="show_stats")]
    ])
    
    await callback.message.edit_text(detailed_text, reply_markup=keyboard)

@dp.callback_query(F.data == "export_users")
async def process_export_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    users = load_users()
    if not users:
        await callback.answer("📭 Foydalanuvchilar ro'yxati bo'sh!", show_alert=True)
        return
    
    # Create users list
    users_text = "📥 Foydalanuvchilar ro'yxati:\n\n"
    for i, user_id in enumerate(users, 1):
        try:
            user = await bot.get_chat(user_id)
            username = user.username or "username yo'q"
            users_text += f"{i}. {user.first_name} (@{username}) - {user_id}\n"
        except:
            users_text += f"{i}. Noma'lum foydalanuvchi - {user_id}\n"
    
    # Split if too long
    if len(users_text) > 4096:
        parts = [users_text[i:i+4096] for i in range(0, len(users_text), 4096)]
        for i, part in enumerate(parts):
            await callback.message.answer(f"{part}\n\nQism {i+1}/{len(parts)}")
    else:
        await callback.message.answer(users_text)
    
    await callback.answer("✅ Foydalanuvchilar ro'yxati yuborildi!")

# Handle all non-command messages for all users
@dp.message(lambda message: not message.text.startswith('/'))
async def handle_code(message: types.Message):
    # Check subscription before processing any message
    if not await check_subscription(message.from_user.id):
        channels = load_channels()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ch["name"], url=ch["invite_link"])]
            for ch in channels
        ] + [[InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_sub")]])
        
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak:",
            reply_markup=keyboard
        )
        return
    
    code = message.text.strip()
    videos = load_videos()
    
    if code in videos["mappings"]:
        # Update statistics properly
        stats = update_daily_stats()  # Get stats with proper structure
        update_code_usage(code)
        update_user_activity(message.from_user.id)
        monthly_stats = update_monthly_stats()  # Get monthly stats with proper structure
        
        today = date.today().isoformat()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Update daily stats
        stats["daily_stats"][today]["codes_used"] += 1
        stats["daily_stats"][today]["users"] += 1
        
        # Update monthly stats
        monthly_stats["monthly_stats"][current_month]["total_codes_used"] += 1
        
        # Save both stats
        save_stats(stats)
        save_stats(monthly_stats)
        
        file_path = videos["mappings"][code]
        try:
            # Determine file type from extension
            ext = os.path.splitext(file_path)[1].lower()
            input_file = FSInputFile(file_path)
            
            if ext in ['.jpg', '.jpeg', '.png']:
                await message.answer_photo(input_file, caption="✅ Fayl topildi")
            elif ext in ['.mp4', '.avi', '.mov']:
                await message.answer_video(input_file, caption="✅ Fayl topildi")
            elif ext in ['.mp3', '.ogg', '.wav']:
                await message.answer_audio(input_file, caption="✅ Fayl topildi")
            elif ext in ['.doc', '.docx', '.pdf', '.txt']:
                await message.answer_document(input_file, caption="✅ Fayl topildi")
            else:
                await message.answer_document(input_file, caption="✅ Fayl topildi")
        except FileNotFoundError:
            await message.answer("❌ Fayl topilmadi! Admin bilan bog'laning.")
    else:
        await message.answer("❌ Kod topilmadi, iltimos tekshirib qayta yuboring")

@dp.callback_query(F.data == "check_sub")
async def process_check_subscription(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Yordam", callback_data="help")]
        ])
        await callback.message.edit_text(
            "✅ Obuna tasdiqlandi!\n\n"
            "👋 Salom! Men video kodlarini qayta ishlash uchun yaratilgan botman.\n\n"
            "Video olish uchun kodni matn ko'rinishida yuboring.",
            reply_markup=keyboard
        )
    else:
        channels = load_channels()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ch["name"], url=ch["invite_link"])]
            for ch in channels
        ] + [[InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_sub")]])
        
        await callback.message.edit_text(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak:",
            reply_markup=keyboard
        )

@dp.callback_query(F.data == "manage_channels")
async def process_manage_channels(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    channels = load_channels()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")],
        [InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="delete_channel")],
        [InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="list_channels")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
    ])
    
    await callback.message.edit_text(
        "📢 Kanal boshqaruvi:\n\n"
        f"Jami kanallar: {len(channels)}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "add_channel")
async def process_add_channel(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 Yangi kanal qo'shish uchun quyidagi formatda yuboring:\n\n"
        "Kanal username: @channel_username\n"
        "Kanal nomi: Kanal nomi\n"
        "Invite link: https://t.me/channel_username\n\n"
        "⚠️ Eslatma: Bot kanalda admin bo'lishi kerak!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
        ])
    )
    await state.set_state(AdminStates.waiting_for_channel)

@dp.callback_query(F.data == "delete_channel")
async def process_delete_channel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    channels = load_channels()
    if not channels:
        await callback.message.edit_text(
            "📭 Kanallar ro'yxati bo'sh!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
            ])
        )
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ch["name"], callback_data=f"del_ch_{ch['id']}")]
        for ch in channels
    ] + [[InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]])
    
    await callback.message.edit_text(
        "🗑 O'chirish uchun kanalni tanlang:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("del_ch_"))
async def process_delete_channel_confirmation(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    channel_id = callback.data[7:]  # Remove "del_ch_" prefix
    channels = load_channels()
    channel = next((ch for ch in channels if ch["id"] == channel_id), None)
    
    if channel:
        delete_channel(channel_id)
        await callback.message.edit_text(
            f"✅ '{channel['name']}' kanali o'chirildi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
            ])
        )
    else:
        await callback.message.edit_text(
            "❌ Kanal topilmadi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
            ])
        )

@dp.callback_query(F.data == "list_channels")
async def process_list_channels(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    channels = load_channels()
    if not channels:
        await callback.message.edit_text(
            "📭 Kanallar ro'yxati bo'sh!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
            ])
        )
        return
    
    channels_list = "\n\n".join([
        f"📢 {ch['name']}\n"
        f"🔗 {ch['invite_link']}"
        for ch in channels
    ])
    
    await callback.message.edit_text(
        f"📋 Mavjud kanallar:\n\n{channels_list}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_channels")]
        ])
    )

@dp.callback_query(F.data == "manage_admins")
async def process_manage_admins(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    admins = load_admins()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_admin")],
        [InlineKeyboardButton(text="🗑 Admin o'chirish", callback_data="delete_admin")],
        [InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="list_admins")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
    ])
    
    await callback.message.edit_text(
        "👥 Admin boshqaruvi:\n\n"
        f"Jami adminlar: {len(admins)}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "add_admin")
async def process_add_admin(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ Yangi admin qo'shish uchun Telegram ID raqamini kiriting:\n\n"
        "⚠️ Eslatma: Telegram ID raqamini olish uchun @userinfobot dan foydalaning",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
        ])
    )
    await state.set_state(AdminStates.waiting_for_add_admin)

@dp.callback_query(F.data == "delete_admin")
async def process_delete_admin(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    admins = load_admins()
    if len(admins) <= 1:
        await callback.message.edit_text(
            "❌ Kamida bitta admin bo'lishi kerak!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
            ])
        )
        return
    
    # Show available admins and ask for input
    admins_list = "\n".join([f"• {admin_id}" for admin_id in admins if admin_id != 5660670674])
    await callback.message.edit_text(
        f"🗑 Admin o'chirish uchun Telegram ID raqamini kiriting:\n\n"
        f"Mavjud adminlar:\n{admins_list}\n\n"
        f"⚠️ Eslatma: Asosiy admin (5660670674) o'chirilmaydi!\n\n"
        f"O'chirish uchun Telegram ID raqamini kiriting:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
        ])
    )
    await state.set_state(AdminStates.waiting_for_delete_admin)

@dp.callback_query(F.data == "list_admins")
async def process_list_admins(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    admins = load_admins()
    if not admins:
        await callback.message.edit_text(
            "📭 Adminlar ro'yxati bo'sh!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
            ])
        )
        return
    
    admins_list = []
    for admin_id in admins:
        try:
            user = await bot.get_chat(admin_id)
            status = "👑 Asosiy admin" if admin_id == 5660670674 else "👤 Admin"
            admins_list.append(f"{status}: {user.first_name} ({admin_id})")
        except:
            admins_list.append(f"👤 Admin: Noma'lum ({admin_id})")
    
    admins_text = "\n".join(admins_list)
    
    await callback.message.edit_text(
        f"📋 Mavjud adminlar:\n\n{admins_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="manage_admins")]
        ])
    )

# Main function
async def main():
    # Create videos directory if it doesn't exist
    os.makedirs("videos", exist_ok=True)
    
    # Start the bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 