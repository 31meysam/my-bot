from aiogram import Bot, Dispatcher, types from aiogram.fsm.storage.memory import MemoryStorage from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder from config import BOT_TOKEN, DEEPSEEK_API_KEY import aiohttp import logging import json import asyncio from typing import Optional, Dict, Any from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig( level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[ logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler() ] ) logger = logging.getLogger(name)

class AIException(Exception): pass

class RateLimitExceeded(AIException): pass

bot = Bot(token=BOT_TOKEN) storage = MemoryStorage() dp = Dispatcher(storage=storage)

class ResponseCache: _instance = None _cache: Dict[str, str] = {}

def __new__(cls):
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance

def get(self, prompt: str) -> Optional[str]:
    return self._cache.get(prompt[:100])

def set(self, prompt: str, response: str):
    self._cache[prompt[:100]] = response

class AIService: def init(self): self.base_url = "https://api.deepseek.com/v1" self.headers = { "Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json", "X-Request-ID": "bot-request-123" } self.cache = ResponseCache() self.timeout = aiohttp.ClientTimeout(total=45, connect=10)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    reraise=True
)
async def _make_api_call(self, payload: dict) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url=f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            ) as response:
                if response.status == 429:
                    raise RateLimitExceeded("Rate limit exceeded")
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"API Error {response.status}: {error}")
                    raise AIException(f"Server error: {response.status}")
                return await response.json()
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {str(e)}")
            raise AIException("Error parsing server response")

async def generate_response(self, prompt: str) -> dict:
    try:
        if cached := self.cache.get(prompt):
            logger.info("Using cached response")
            return {"choices": [{"message": {"content": cached}}]}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2500,
            "top_p": 0.9,
            "frequency_penalty": 0.2
        }
        data = await self._make_api_call(payload)
        if response := data.get("choices", [{}])[0].get("message", {}).get("content"):
            self.cache.set(prompt, response)
        return data
    except RateLimitExceeded:
        return {"error": "⚠️ Rate limit exceeded. Please wait a minute."}
    except asyncio.TimeoutError:
        return {"error": "⏳ Request timeout. Please try again."}
    except AIException as e:
        return {"error": f"⚠️ System error: {str(e)}"}
    except Exception as e:
        logger.exception("Unexpected error in AI service")
        return {"error": "⚠️ Unexpected error occurred."}

