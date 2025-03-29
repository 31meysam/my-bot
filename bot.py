import os
import logging
# تغییر خط import به این شکل:
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import setup_application  # برای webhook
from aiogram.client.default import DefaultBotProperties  # تنظیمات پیش‌فرض
# --- تنظیمات اولیه ---
load_dotenv()

# لاگ‌گیری پیشرفته
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تنظیمات API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# کلاینت‌ها
bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# --- دستورات ربات ---
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    welcome_text = """
    🚀 <b>ربات هوش مصنوعی پیشرفته</b>
    
    • ارسال پیام: چت با GPT-4o
    • /img <توضیحات>: تولید تصویر با DALL·E 3
    • /ask <سوال>: پاسخ دقیق به سوالات تخصصی
    
    <i>از قابلیت‌های هوش مصنوعی جدید OpenAI استفاده می‌کند</i>
    """
    await message.reply(welcome_text)

# --- پردازش هوش مصنوعی ---
async def get_ai_response(prompt: str) -> Optional[str]:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except APIConnectionError as e:
        logger.error(f"Connection error: {e}")
        return None
    except APIError as e:
        logger.error(f"API error: {e}")
        return None

# --- هندلرهای پیام ---
@dp.message_handler(commands=['ask'])
async def handle_ask(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("⚠ لطفاً بعد از /ask سوال خود را مطرح کنید")
        return
    
    await message.answer_chat_action("typing")
    
    response = await get_ai_response(prompt)
    if response:
        await message.reply(response)
    else:
        await message.reply("⛔ خطا در ارتباط با سرور هوش مصنوعی")

@dp.message_handler(commands=['img'])
async def handle_image_gen(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("⚠ لطفاً بعد از /img توضیح تصویر را وارد کنید")
        return
    
    try:
        await message.answer_chat_action("upload_photo")
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="hd"
        )
        
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=response.data[0].url,
            caption=f"🖼 تصویر تولید شده برای: <i>{prompt[:100]}...</i>"
        )
    except Exception as e:
        logger.error(f"Image gen error: {e}")
        await message.reply(f"⚠ خطا در تولید تصویر: {str(e)}")

@dp.message_handler()
async def handle_text(message: types.Message):
    await message.answer_chat_action("typing")
    response = await get_ai_response(message.text)
    if response:
        await message.reply(response)
    else:
        await message.reply("⛔ سرویس موقتاً در دسترس نیست")

# --- اجرای ربات ---
if __name__ == '__main__':
    try:
        logger.info("Starting bot...")
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.critical(f"Bot failed: {e}")
