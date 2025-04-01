import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # توکن ربات
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # کلید API هوش مصنوعی
