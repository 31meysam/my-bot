from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN, DEEPSEEK_API_KEY
import aiohttp
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ========== دکمه‌های پیشرفته ========== #
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("💬 چت با هوش مصنوعی"))
    keyboard.add(KeyboardButton("ℹ️ اطلاعات ربات"))
    keyboard.add(KeyboardButton("🔍 جستجو در ویکی‌پدیا"))
    return keyboard

def get_inline_keyboard():
    buttons = [
        [InlineKeyboardButton("پشتیبانی 📞", url="t.me/example_support")],
        [InlineKeyboardButton("سورس کد 🔗", url="github.com/your_repo")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== ارتباط با هوش مصنوعی (DeepSeek) ========== #
async def get_ai_response(prompt: str) -> str:
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers) as resp:
            response = await resp.json()
            return response["choices"][0]["message"]["content"]

# ========== دستورات ربات ========== #
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = "👋 **به ربات هوش مصنوعی خوش آمدید!**\n\n🔹 برای شروع چت، پیام خود را ارسال کنید."
    await message.answer(welcome_text, reply_markup=get_main_menu())

@dp.message_handler(lambda msg: msg.text == "💬 چت با هوش مصنوعی")
async def ai_chat_mode(message: types.Message):
    await message.answer("💡 **حالت چت فعال شد!**\nهر پیامی بفرستید تا هوش مصنوعی پاسخ دهد.")

@dp.message_handler(lambda msg: msg.text == "ℹ️ اطلاعات ربات")
async def show_bot_info(message: types.Message):
    info_text = "🤖 **نام ربات:** هوش مصنوعی پیشرفته\n\n🔹 **نسخه:** 1.0\n🔹 **سازنده:** شما"
    await message.answer(info_text, reply_markup=get_inline_keyboard())

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    ai_response = await get_ai_response(message.text)
    await message.answer(ai_response)

# ========== اجرای ربات ========== #
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
