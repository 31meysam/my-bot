from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import openai
import os
from dotenv import load_dotenv

# تنظیمات اولیه
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_KEY

# پاسخ به /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("""
    سلام! من ربات هوشمند شما هستم 🤖
    • می‌توانم مثل ChatGPT چت کنم
    • با دستور /image عکس تولید کنم
    """)

# پردازش پیام‌ها با GPT
@dp.message_handler()
async def chat(message: types.Message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message.text}]
    )
    await message.reply(response.choices[0].message['content'])

# تولید عکس با DALL·E
@dp.message_handler(commands=['image'])
async def gen_image(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("⚠ لطفاً بعد از /image توضیح عکس را بنویسید.")
        return
    
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    await bot.send_photo(message.chat.id, response['data'][0]['url'])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
