from aiogram import Bot, Dispatcher, types
from aiogram.types import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import BOT_TOKEN, DEEPSEEK_API_KEY
import aiohttp
import logging
import json
import asyncio
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 1. تنظیمات پیشرفته لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2. کلاس مدیریت خطاهای سفارشی
class AIException(Exception):
    """خطاهای اختصاصی سیستم هوش مصنوعی"""
    pass

class RateLimitExceeded(AIException):
    """خطای محدودیت نرخ"""
    pass

# 3. تنظیمات پیشرفته ربات
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# 4. سیستم کشینگ پیشرفته
class ResponseCache:
    """سیستم کش برای ذخیره پاسخ‌های متداول"""
    _instance = None
    _cache: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, prompt: str) -> Optional[str]:
        return self._cache.get(prompt[:100])  # استفاده از 100 کاراکتر اول به عنوان کلید

    def set(self, prompt: str, response: str):
        self._cache[prompt[:100]] = response

# 5. سرویس هوش مصنوعی با قابلیت بازآزمایی خودکار
class AIService:
    """سرویس پیشرفته ارتباط با DeepSeek AI"""
    
    def __init__(self):
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
            "X-Request-ID": "bot-request-123"  # برای رهگیری بهتر
        }
        self.cache = ResponseCache()
        self.timeout = aiohttp.ClientTimeout(total=45, connect=10)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _make_api_call(self, payload: dict) -> Dict[str, Any]:
        """تماس پایه با API با قابلیت بازآزمایی"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url=f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitExceeded("محدودیت نرخ مصرف")
                    
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"API Error {response.status}: {error}")
                        raise AIException(f"خطای سرور: {response.status}")

                    return await response.json()

            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {str(e)}")
                raise AIException("خطای پردازش پاسخ سرور")

    async def generate_response(self, prompt: str) -> dict:
        """تولید پاسخ با مدیریت کامل خطاها"""
        try:
            # 1. بررسی کش
            if cached := self.cache.get(prompt):
                logger.info("Using cached response")
                return {"choices": [{"message": {"content": cached}}]}

            # 2. ساختار درخواست
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2500,
                "top_p": 0.9,
                "frequency_penalty": 0.2
            }

            # 3. ارسال درخواست
            data = await self._make_api_call(payload)
            
            # 4. ذخیره در کش
            if response := data.get("choices", [{}])[0].get("message", {}).get("content"):
                self.cache.set(prompt, response)
            
            return data

        except RateLimitExceeded:
            return {"error": "⚠️ تعداد درخواست‌ها بیش از حد مجاز است. لطفاً 1 دقیقه صبر کنید."}
        except asyncio.TimeoutError:
            return {"error": "⏳ زمان انتظار به پایان رسید. لطفاً دوباره تلاش کنید."}
        except AIException as e:
            return {"error": f"⚠️ خطای سیستم: {str(e)}"}
        except Exception as e:
            logger.exception("Unexpected error in AI service")
            return {"error": "⚠️ خطای غیرمنتظره در پردازش درخواست"}

# 6. سیستم مدیریت حالت‌های کاربر
class UserStateManager:
    """مدیریت پیشرفته حالت‌های کاربر"""
    
    def __init__(self):
        self.user_states = {}

    def set_state(self, user_id: int, state: str):
        self.user_states[user_id] = state

    def get_state(self, user_id: int) -> str:
        return self.user_states.get(user_id, "default")

state_manager = UserStateManager()

# 7. ساختارهای رابط کاربری پیشرفته
def build_main_menu() -> types.ReplyKeyboardMarkup:
    """منوی اصلی با طراحی واکنش‌گرا"""
    builder = ReplyKeyboardBuilder()
    buttons = [
        ("💬 چت هوشمند", "start_chat"),
        ("ℹ️ اطلاعات ربات", "bot_info"),
        ("⚙️ تنظیمات", "settings"),
        ("📊 آمار", "stats"),
        ("🛠️ ابزارها", "tools"),
        ("📚 راهنما", "help")
    ]
    
    for text, callback in buttons:
        builder.add(types.KeyboardButton(text=text))
    
    builder.adjust(2, 2, 2)
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="گزینه مورد نظر را انتخاب کنید..."
    )

def build_ai_settings_menu() -> types.InlineKeyboardMarkup:
    """منوی تنظیمات پیشرفته هوش مصنوعی"""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🔧 تغییر مدل", callback_data="change_model"),
        types.InlineKeyboardButton(text="⚖️ تنظیم دقت", callback_data="set_temp")
    )
    builder.row(
        types.InlineKeyboardButton(text="📏 طول پاسخ", callback_data="set_max_tokens"),
        types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="main_menu")
    )
    return builder.as_markup()

# 8. هندلرهای هوشمند
@dp.message(commands=['start', 'help'])
async def handle_start(message: types.Message):
    """مدیریت دستور شروع با تجربه کاربری غنی"""
    user = message.from_user
    welcome_msg = f"""
    🌟 <b>سلام {user.first_name}!</b> 🌟

🤖 به پیشرفته‌ترین ربات هوش مصنوعی خوش آمدید!

🔹 <u>امکانات اصلی:</u>
• چت هوشمند با DeepSeek AI
• تنظیمات پیشرفته مدل
• پشتیبانی 24/7
• سیستم گزارش خودکار

📌 لطفاً از منوی زیر انتخاب کنید:
    """
    
    await message.answer(
        text=welcome_msg,
        reply_markup=build_main_menu(),
        disable_web_page_preview=True
    )
    state_manager.set_state(user.id, "main_menu")

@dp.message(lambda msg: msg.text == "💬 چت هوشمند")
async def enable_chat_mode(message: types.Message):
    """فعال‌سازی حالت گفتگوی پیشرفته"""
    user = message.from_user
    state_manager.set_state(user.id, "chat_mode")
    
    await message.answer(
        text="💡 <b>حالت گفتگوی هوشمند فعال شد!</b>\n\n"
             "• می‌توانید سوالات تخصصی بپرسید\n"
             "• برای بازگشت /cancel ارسال کنید\n"
             "• حداکثر طول پیام: 4000 کاراکتر",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

# 9. مدیریت مرکزی پیام‌ها
@dp.message()
async def handle_all_messages(message: types.Message):
    """سیستم یکپارچه پردازش پیام‌ها"""
    user = message.from_user
    # 9. مدیریت مرکزی پیام‌ها
@dp.message()
async def handle_all_messages(message: types.Message):
    """سیستم یکپارچه پردازش پیام‌ها"""
    user = message.from_user
    current_state = state_manager.get_state(user.id)
    
    try:
        # 1. اعتبارسنجی اولیه
        if not message.text or len(message.text) > 4000:
            await message.answer("⚠️ پیام باید بین 1 تا 4000 کاراکتر باشد")
            return

        # 2. نمایش وضعیت تایپ
        await bot.send_chat_action(user.id, 'typing')

        # 3. پردازش بر اساس حالت کاربر
        if current_state == "chat_mode":
            ai_service = AIService()
            result = await ai_service.generate_response(message.text)
            
            if 'error' in result:
                await message.answer(result['error'])
            else:
                response = result['choices'][0]['message']['content']
                await message.answer(response[:4000])  # محدودیت طول پاسخ

        else:
            await message.answer("لطفاً از منوی اصلی انتخاب کنید:", reply_markup=build_main_menu())

    except Exception as e:
        logger.exception(f"Error processing message from {user.id}")
        await message.answer("⚠️ خطای سیستمی رخ داد. لطفاً بعداً تلاش کنید.")

# 10. سیستم مانیتورینگ و راه‌اندازی
async def startup():
    """عملیات آغازین پیش از راه‌اندازی"""
    logger.info("Initializing AI Telegram Bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot initialized successfully")

async def shutdown():
    """عملیات پایانی قبل از خاموشی"""
    logger.info("Shutting down bot...")
    await bot.session.close()
    logger.info("Bot shutdown completed")

async def main():
    """نقطه ورود اصلی برنامه"""
    try:
        await startup()
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        await shutdown()

if __name__ == '__main__':
    asyncio.run(main())
