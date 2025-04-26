from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

API_URL = "http://localhost:8001"
TOKEN = "7879703019:AAHgq3YSlU4wug2L0vC5aSf57XX5MvFfO_U"

async def start(update: Update, context):
    await update.message.reply_text(
        "Привет! Отправь трату в формате:\n"
        "/add 500 еда кофе"
    )

async def add_transaction(update: Update, context):
    try:
        _, amount, category, *description = update.message.text.split()
        data = {
            "amount": float(amount),
            "category": category,
            "description": " ".join(description) if description else None
        }
        response = requests.post(f"{API_URL}/transactions/", json=data)
        await update.message.reply_text("✅ Трата сохранена!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_transaction))
    app.run_polling()

if __name__ == "__main__":
    run_bot()