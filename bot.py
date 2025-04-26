from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
from datetime import datetime

API_URL = "http://localhost:8001"  # Убедитесь, что сервер работает на этом порту
TOKEN = "7879703019:AAHgq3YSlU4wug2L0vC5aSf57XX5MvFfO_U"

async def start(update: Update, context):
    await update.message.reply_text(
        "💰 Финансовый трекер\n\n"
        "Доступные команды:\n"
        "/add <сумма> <категория> [описание] - добавить трату\n"
        "/list - показать все траты\n"
        "/stats - статистика (в разработке)"
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

async def list_transactions(update: Update, context):
    try:
        response = requests.get(f"{API_URL}/transactions/")
        transactions = response.json()
        
        if not transactions:
            await update.message.reply_text("📭 Список трат пуст")
            return
            
        message = "📋 История трат:\n\n"
        for idx, tr in enumerate(transactions, 1):
            date = datetime.strptime(tr['date'], "%Y-%m-%d").strftime("%d.%m.%Y")
            message += (
                f"{idx}. {tr['amount']} ₽ - {tr['category']}\n"
                f"   Описание: {tr.get('description', 'нет')}\n"
                f"   Дата: {date}\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении трат: {e}")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_transaction))
    app.add_handler(CommandHandler("list", list_transactions))
    
    app.run_polling()

if __name__ == "__main__":
    run_bot()