from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN, DEEPSEEK_API_KEY
import aiohttp
import logging
import json

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ========== دکمه‌های پیشرفته ========== #
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
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
                logger.info(f"API Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
                
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
@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 **به ربات هوش مصنوعی خوش آمدید!**\n\n"
        "🔹 برای شروع چت، پیام خود را ارسال کنید یا از دکمه‌های زیر استفاده نمایید:\n"
        "• /start - نمایش این پیام\n"
        "• /help - راهنمای استفاده\n"
        "• 💬 چت با هوش مصنوعی\n"
        "• ℹ️ اطلاعات ربات"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

@dp.message_handler(lambda msg: msg.text == "💬 چت با هوش مصنوعی")
async def ai_chat_mode(message: types.Message):
    await message.answer(
        "💡 **حالت چت فعال شد!**\n"
        "هم اکنون می‌توانید سوالات خود را بپرسید.\n"
        "برای بازگشت به منوی اصلی /start را ارسال کنید.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message_handler(lambda msg: msg.text == "ℹ️ اطلاعات ربات")
async def show_bot_info(message: types.Message):
    info_text = (
        "🤖 **نام ربات:** هوش مصنوعی پیشرفته\n\n"
        "🔹 **نسخه:** 2.0\n"
        "🔹 **پلتفرم:** Telegram Bot\n"
        "🔹 **موتور هوش مصنوعی:** DeepSeek Chat\n"
        "🔹 **سازنده:** شما\n\n"
        "برای پشتیبانی یا گزارش مشکل از دکمه‌های زیر استفاده کنید:"
    )
    await message.answer(info_text, reply_markup=get_inline_keyboard())

@dp.callback_query_handler(lambda c: c.data == "help")
async def process_callback_help(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📚 **راهنمای استفاده:**\n\n"
        "1. برای شروع چت، دکمه «💬 چت با هوش مصنوعی» را انتخاب کنید\n"
        "2. سوال خود را به صورت متنی ارسال نمایید\n"
        "3. ربات در سریع‌ترین زمان پاسخ خواهد داد\n"
        "4. برای بازگشت به منوی اصلی /start را ارسال کنید\n\n"
        "⚠️ توجه: این ربات از هوش مصنوعی DeepSeek استفاده می‌کند",
        reply_markup=get_main_menu()
    )

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    try:
        if not message.text:
            await message.answer("لطفاً فقط متن ارسال کنید.")
            return

        # نمایش وضعیت "در حال تایپ..."
        await bot.send_chat_action(message.chat.id, "typing")
        
        ai_response = await get_ai_response(message.text)
        await message.answer(ai_response)

    except Exception as e:
        logger.error(f"Error in message handling: {str(e)}")
        await message.answer("⚠️ خطایی در پردازش درخواست شما رخ داد. لطفاً بعداً تلاش کنید.")

# ========== اجرای ربات ========== #
if __name__ == '__main__':
    logger.info("Starting bot...")
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
