from aiogram import Bot, Dispatcher, executor
TOKEN = "7940617171:AAH6gbaKQzwZKMPxF98oBEFVZeKoaolTUWQ" # توکن ربات شما

bot = Bot(TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message):
    await message.reply("سلام! من ربات شما هستم :)")

executor.start_polling(dp)
