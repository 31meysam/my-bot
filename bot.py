from aiogram import Bot, Dispatcher
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import os

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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

import sqlite3

conn = sqlite3.connect('chat.db')
cursor = conn.cursor()

# ذخیره پیام‌ها
def save_message(user_id, text):
    cursor.execute("INSERT INTO chats VALUES (?, ?)", (user_id, text))
    conn.commit()
if name == 'main':
    executor.start_polling(dp, skip_updates=True)
