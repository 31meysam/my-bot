import logging import asyncio from aiogram import Bot, Dispatcher, types from config import BOT_TOKEN, DEEPSEEK_API_KEY import aiohttp

logging.basicConfig(level=logging.INFO)

async def get_ai_response(prompt): url = "https://api.deepseek.com/v1/chat/completions" headers = { "Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json" } data = { "model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}] }

async with aiohttp.ClientSession() as session:
    async with session.post(url, json=data, headers=headers) as response:
        result = await response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")

async def handle_message(message: types.Message): response = await get_ai_response(message.text) await message.answer(response)

async def main(): bot = Bot(token=BOT_TOKEN) dp = Dispatcher() dp.message.register(handle_message)

try:
    await dp.start_polling(bot)
finally:
    await bot.close()

if name == "main": asyncio.run(main())

