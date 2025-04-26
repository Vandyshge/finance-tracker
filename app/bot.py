from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime

API_URL = "http://localhost:8001"
TOKEN = "7879703019:AAHgq3YSlU4wug2L0vC5aSf57XX5MvFfO_U"

async def start(update: Update, context):
    await update.message.reply_text(
        "💰 Финансовый трекер\n\n"
        "Доступные команды:\n"
        "/add <сумма> <категория> [описание] [дата] - добавить трату\n"
        "/list - показать все траты\n"
    )

async def add_transaction(update: Update, context):
    try:
        args = update.message.text.split()
        if len(args) < 3:
            await update.message.reply_text("❌ Формат: /add <сумма> <категория> [описание] [дата в формате ДД.ММ.ГГГГ]")
            return

        amount = float(args[1])
        category = args[2]
        description = " ".join(args[3:-1]) if len(args) > 3 else None
        date_str = args[-1] if len(args) > 3 and "." in args[-1] else datetime.now().strftime("%d.%m.%Y")
        print(date_str)

        try:
            date = datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            date = datetime.now().strftime("%Y-%m-%d")
            description = " ".join(args[3:]) if len(args) > 3 else None
        print(date)

        data = {
            "amount": amount,
            "category": category,
            "description": description,
            "transaction_date": date
        }
        
        response = requests.post(f"{API_URL}/transactions/", json=data)
        await update.message.reply_text(f"✅ Трата {amount}₽ на {category} сохранена!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

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
                f"   Дата: {date}\n"
                f"   ID: {tr['id']}\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении трат: {str(e)}")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_transaction))
    app.add_handler(CommandHandler("list", list_transactions))
    app.run_polling()

if __name__ == "__main__":
    run_bot()