import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Step 1: Put your bot token here
TOKEN = '7940617171:AAFf36mEF_-_GFgXGN4YE3kQN06-n8LYux0'  # Replace with your actual bot token

# Step 2: Scrape stock price from Yahoo Finance
def scrape_stock_price(symbol: str):
    url = f'https://finance.yahoo.com/quote/{symbol}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    try:
        price = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'}).text
        return price
    except Exception:
        return None

# Step 3: Define the Telegram command
async def stock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /stock SYMBOL\nExample: /stock AAPL")
        return

    symbol = context.args[0].upper()
    price = scrape_stock_price(symbol)

    if price:
        await update.message.reply_text(f"The current price of {symbol} is ${price}")
    else:
        await update.message.reply_text("Sorry, couldn't fetch the price. Check the symbol and try again.")

# Step 4: Run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("stock", stock_handler))
    print("Bot is running...")
    app.run_polling()
