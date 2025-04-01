from aiogram import Bot, Dispatcher, types from aiogram.contrib.middlewares.logging import LoggingMiddleware from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton from config import BOT_TOKEN, DEEPSEEK_API_KEY import aiohttp import logging import json import asyncio from typing import Optional, Dict, Any from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

تنظیمات لاگ‌گیری

logging.basicConfig(level=logging.INFO) logger = logging.getLogger(name)

bot = Bot(token=BOT_TOKEN) dp = Dispatcher(bot) dp.middleware.setup(LoggingMiddleware())

class AIException(Exception): pass

class RateLimitExceeded(AIException): pass

class ResponseCache: _instance = None _cache: Dict[str, str] = {}

def __new__(cls):
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance

def get(self, prompt: str) -> Optional[str]:
    return self._cache.get(prompt[:100])

def set(self, prompt: str, response: str):
    self._cache[prompt[:100]] = response

class AIService: def init(self): self.base_url = "https://api.deepseek.com/v1" self.headers = { "Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json" } self.cache = ResponseCache() self.timeout = aiohttp.ClientTimeout(total=45, connect=10)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)))
async def _make_api_call(self, payload: dict) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url=f"{self.base_url}/chat/completions", json=payload, headers=self.headers, timeout=self.timeout) as response:
            if response.status == 429:
                raise RateLimitExceeded("Rate limit exceeded")
            return await response.json()

async def generate_response(self, prompt: str) -> dict:
    if cached := self.cache.get(prompt):
        return {"choices": [{"message": {"content": cached}}]}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2500}
    data = await self._make_api_call(payload)
    if response := data.get("choices", [{}])[0].get("message", {}).get("content"):
        self.cache.set(prompt, response)
    return data

def build_main_menu() -> ReplyKeyboardMarkup: keyboard = ReplyKeyboardMarkup(resize_keyboard=True) buttons = ["💬 چت هوشمند", "ℹ️ اطلاعات ربات", "⚙️ تنظیمات"] keyboard.add(*(KeyboardButton(text) for text in buttons)) return keyboard

@dp.message_handler(commands=['start', 'help']) async def handle_start(message: types.Message): await message.reply("به ربات خوش آمدید!", reply_markup=build_main_menu())

@dp.message_handler(lambda message: message.text == "💬 چت هوشمند") async def chat_mode(message: types.Message): ai_service = AIService() response = await ai_service.generate_response("سلام") await message.reply(response["choices"][0]["message"]["content"])

async def main(): await dp.start_polling()

if name == 'main': asyncio.run(main())

