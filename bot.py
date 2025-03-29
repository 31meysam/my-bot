from aiogram import Bot, Dispatcher, executor  # خط ۱
from aiogram import types  # خط ۲
import openai
import os
from dotenv import load_dotenv
# بقیه کدها بدون تغییر..
# تنظیمات اولیه
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_KEY

# دستورات ربات
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("""
    🤖 ربات هوش مصنوعی فعال شد!
    /gpt <پیام> - چت با هوش مصنوعی
    /img <توضیح> - تولید عکس
    """)

# پردازش پیام‌های متنی
@dp.message_handler(commands=['gpt'])
async def chat_gpt(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("لطفاً پس از /gpt پیام خود را بنویسید")
        return
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        await message.reply(response.choices[0].message['content'])
    except Exception as e:
        await message.reply(f"خطا: {str(e)}")

# تولید عکس
@dp.message_handler(commands=['img'])
async def generate_image(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("لطفاً پس از /img توضیح عکس را بنویسید")
        return
    
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        await bot.send_photo(message.chat.id, response['data'][0]['url'])
    except Exception as e:
        await message.reply(f"خطا: {str(e)}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
