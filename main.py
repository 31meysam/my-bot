import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import BOT_TOKEN, DEEPSEEK_API_KEY
import aiohttp

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== دکمه‌های پیشرفته ========== #
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("💬 چت با هوش مصنوعی"),
        KeyboardButton("ℹ️ اطلاعات ربات"),
        KeyboardButton("🔍 جستجو در ویکی‌پدیا"),
        KeyboardButton("🆘 راهنما")
    )
    return keyboard

def get_inline_keyboard():
    buttons = [
        [InlineKeyboardButton("پشتیبانی 📞", url="t.me/example_support")],
        [InlineKeyboardButton("سورس کد 🔗", url="github.com/your_repo")],
        [InlineKeyboardButton("آموزش استفاده 📚", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== ارتباط با هوش مصنوعی (DeepSeek) ========== #
async def get_ai_response(prompt: str) -> str:
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"API Error: {resp.status} - {error_text}")
                    return f"خطا در ارتباط با سرور (کد {resp.status})"

                response = await resp.json()
                if "choices" in response and len(response["choices"]) > 0:
                    return response["choices"][0]["message"]["content"]
                elif "error" in response:
                    return f"خطا از سمت هوش مصنوعی: {response['error']}"
                else:
                    return "پاسخ دریافتی غیرمنتظره بود. لطفاً دوباره تلاش کنید."
    except aiohttp.ClientError as e:
        logger.error(f"Connection Error: {str(e)}")
        return "خطا در اتصال به سرور هوش مصنوعی"
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        return "خطای غیرمنتظره رخ داد"

# ========== دستورات ربات ========== #
@dp.message(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 **به ربات هوش مصنوعی خوش آمدید!**\n\n"
        "🔹 برای شروع چت، پیام خود را ارسال کنید یا از دکمه‌های زیر استفاده نمایید:\n"
        "• /start - نمایش این پیام\n"
        "• /help - راهنمای استفاده"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

@dp.message(lambda msg: msg.text == "💬 چت با هوش مصنوعی")
async def ai_chat_mode(message: types.Message):
    await message.answer(
        "💡 **حالت چت فعال شد!**\n"
        "سوالات خود را بپرسید.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(lambda msg: msg.text == "ℹ️ اطلاعات ربات")
async def show_bot_info(message: types.Message):
    info_text = (
        "🤖 **نام ربات:** هوش مصنوعی پیشرفته\n"
        "🔹 **نسخه:** 2.0\n"
        "🔹 **موتور هوش مصنوعی:** DeepSeek Chat\n"
        "🔹 **سازنده:** شما"
    )
    await message.answer(info_text, reply_markup=get_inline_keyboard())

@dp.callback_query(lambda c: c.data == "help")
async def process_callback_help(callback_query: types.CallbackQuery):
    await callback_query.answer("راهنمای استفاده")
    await bot.send_message(
        callback_query.from_user.id,
        "📚 **راهنمای استفاده:**\n"
        "1. دکمه «💬 چت با هوش مصنوعی» را انتخاب کنید.\n"
        "2. پیام خود را ارسال کنید.\n"
        "3. منتظر پاسخ باشید."
    )

@dp.message()
async def handle_all_messages(message: types.Message):
    try:
        if not message.text:
            await message.answer("لطفاً فقط متن ارسال کنید.")
            return

        await bot.send_chat_action(message.chat.id, "typing")
        ai_response = await get_ai_response(message.text)
        await message.answer(ai_response)

    except Exception as e:
        logger.error(f"Error in message handling: {str(e)}")
        await message.answer("⚠️ خطایی در پردازش درخواست شما رخ داد.")

# ========== اجرای ربات ========== #
async def main():
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
