from aiogram import Bot, Dispatcher, executor
  import os

  TOKEN = os.getenv("TOKEN")  # توکن از محیط اجرا گرفته می‌شود
  bot = Bot(token=TOKEN)
  dp = Dispatcher(bot)

  @dp.message_handler(commands=['start'])
  async def start(message):
      await message.reply("ربات شما با موفقیت فعال شد! 🤖")

  if __name__ == '__main__':
      executor.start_polling(dp)
