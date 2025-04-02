import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F # F برای فیلتر کردن پیام‌ها
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode, ChatAction # برای ارسال وضعیت typing

# فرض می‌کنیم توکن‌ها در فایل config.py تعریف شده‌اند
try:
    from config import BOT_TOKEN, DEEPSEEK_API_KEY
except ImportError:
    print("خطا: فایل config.py یافت نشد یا متغیرهای BOT_TOKEN و DEEPSEEK_API_KEY در آن تعریف نشده‌اند.")
    exit()

# تنظیمات اولیه لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL و مدل API دیپ‌سیک
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat" # یا مدل مورد نظر شما

# ایجاد یک سشن aiohttp برای استفاده مجدد
# بهتر است سشن در بیرون از تابع درخواست ساخته شود تا کارایی بهتر باشد
aiohttp_session = None

async def get_aiohttp_session():
    """ایجاد یا بازگرداندن سشن aiohttp موجود."""
    global aiohttp_session
    if aiohttp_session is None or aiohttp_session.closed:
        aiohttp_session = aiohttp.ClientSession()
        logging.info("aiohttp.ClientSession جدید ایجاد شد.")
    return aiohttp_session

async def close_aiohttp_session():
    """بستن سشن aiohttp در صورت وجود."""
    global aiohttp_session
    if aiohttp_session and not aiohttp_session.closed:
        await aiohttp_session.close()
        logging.info("aiohttp.ClientSession بسته شد.")
        aiohttp_session = None

async def get_ai_response(prompt: str) -> str:
    """
    دریافت پاسخ از API دیپ‌سیک با مدیریت خطای بهتر.
    """
    session = await get_aiohttp_session()
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}]
        # می‌توانید پارامترهای دیگر مثل max_tokens, temperature را اینجا اضافه کنید
    }

    try:
        # اضافه کردن timeout برای جلوگیری از انتظار بی‌نهایت
        async with session.post(DEEPSEEK_API_URL, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
            # بررسی وضعیت HTTP
            if response.status == 200:
                result = await response.json()
                # بررسی دقیق‌تر ساختار پاسخ
                choices = result.get("choices")
                if choices and isinstance(choices, list) and len(choices) > 0:
                    message_content = choices[0].get("message", {}).get("content")
                    if message_content:
                        return message_content
                    else:
                        logging.error(f"ساختار پاسخ دیپ‌سیک غیرمنتظره بود (content خالی): {result}")
                        return "پاسخی از هوش مصنوعی دریافت نشد، اما ساختار پاسخ متفاوت بود."
                else:
                    logging.error(f"ساختار پاسخ دیپ‌سیک غیرمنتظره بود (choices نامعتبر): {result}")
                    return "ساختار پاسخ هوش مصنوعی نامعتبر بود."
            else:
                # ثبت خطای HTTP و متن خطا در صورت وجود
                error_text = await response.text()
                logging.error(f"خطای API دیپ‌سیک: وضعیت {response.status}, پیام: {error_text}")
                return f"متاسفانه خطایی در ارتباط با سرویس هوش مصنوعی رخ داد (کد: {response.status})."

    except aiohttp.ClientError as e:
        logging.exception(f"خطای شبکه یا کلاینت aiohttp هنگام تماس با دیپ‌سیک: {e}")
        return "مشکل در اتصال به سرویس هوش مصنوعی. لطفاً دوباره تلاش کنید."
    except asyncio.TimeoutError:
        logging.warning("پاسخ از API دیپ‌سیک در زمان مقرر دریافت نشد (Timeout).")
        return "سرویس هوش مصنوعی دیر پاسخ داد. لطفاً دوباره تلاش کنید."
    except Exception as e:
        # ثبت هرگونه خطای پیش‌بینی نشده دیگر
        logging.exception(f"خطای پیش‌بینی نشده در get_ai_response: {e}")
        return "یک خطای داخلی پیش‌بینی نشده رخ داد."

# هندلر برای دستور /start
async def handle_start(message: types.Message):
    await message.answer(f"سلام {message.from_user.first_name}!\nپیام خود را برای من ارسال کنید تا با استفاده از DeepSeek به آن پاسخ دهم.")

# هندلر اصلی برای پیام‌های متنی
async def handle_text_message(message: types.Message, bot: Bot): # اضافه کردن bot به پارامترها
    user_prompt = message.text
    chat_id = message.chat.id

    # ارسال وضعیت "typing" به کاربر
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    logging.info(f"دریافت پیام از کاربر {message.from_user.id} در چت {chat_id}: {user_prompt[:50]}...") # لاگ کردن بخشی از پیام

    # دریافت پاسخ از هوش مصنوعی
    response_text = await get_ai_response(user_prompt)

    logging.info(f"ارسال پاسخ به کاربر {message.from_user.id}: {response_text[:50]}...")

    # ارسال پاسخ به کاربر
    await message.answer(response_text, parse_mode=ParseMode.MARKDOWN) # می‌توانید از Markdown برای فرمت‌دهی بهتر استفاده کنید

async def main():
    # ایجاد Bot instance با parse_mode پیش‌فرض (اختیاری)
    # bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # ثبت هندلرها
    dp.message.register(handle_start, CommandStart()) # هندلر برای /start
    # ثبت هندلر پیام متنی - استفاده از F برای فیلتر کردن فقط پیام‌های متنی
    dp.message.register(handle_text_message, F.text)

    logging.info("ربات در حال شروع شدن است...")

    try:
        # شروع polling - bot instance به صورت خودکار به هندلرها پاس داده می‌شود اگر لازم باشد
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(f"خطای اصلی در اجرای ربات: {e}")
    finally:
        # بستن سشن aiohttp قبل از خروج
        await close_aiohttp_session()
        # بستن ارتباط ربات
        await bot.close()
        logging.info("ربات متوقف شد.")

# اجرای تابع اصلی به صورت ناهمگام
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("خروج توسط کاربر (Ctrl+C)")
