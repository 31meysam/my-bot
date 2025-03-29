from aiogram import Bot, Dispatcher, types, executor
from openai import OpenAI
import os
from dotenv import load_dotenv

# تنظیمات اولیه
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
client = OpenAI(api_key=OPENAI_KEY)  # تغییر به شیء client

# دستور /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("""
    🤖 ربات هوشمند با GPT-4o فعال شد!
    • هر پیامی بفرستید تا پاسخ دهم
    • /img برای تولید عکس
    """)

# پردازش پیام‌ها با GPT-4o
@dp.message_handler()
async def chat_gpt(message: types.Message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # استفاده از مدل جدید
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7
        )
        await message.reply(response.choices[0].message.content)
    except Exception as e:
        await message.reply(f"⚠ خطا: {str(e)}")

# تولید عکس با DALL·E 3
@dp.message_handler(commands=['img'])
async def generate_image(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("لطفاً بعد از /img توضیح عکس را بنویسید")
        return
    
    try:
        response = client.images.generate(
            model="dall-e-3",  # مدل جدید DALL·E 3
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard"
        )
        await bot.send_photo(message.chat.id, response.data[0].url)
    except Exception as e:
        await message.reply(f"⚠ خطا در تولید عکس: {str(e)}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
