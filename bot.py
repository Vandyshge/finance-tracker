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
        "/delete - удалить трату\n"
    )

async def add_transaction(update: Update, context):
    try:
        args = update.message.text.split()
        if len(args) < 3:
            await update.message.reply_text("❌ Формат: /add <сумма> <категория> [описание] [дата в формате ДД.ММ.ГГГГ]")
            return

        amount = float(args[1])
        category = args[2]
        
        # Парсим оставшиеся аргументы
        description_parts = []
        date_str = None
        
        for arg in args[3:]:
            if '.' in arg and len(arg.split('.')) == 3:
                try:
                    datetime.strptime(arg, "%d.%m.%Y")
                    date_str = arg
                    break
                except ValueError:
                    pass
            description_parts.append(arg)
        
        date = datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d") if date_str else datetime.now().strftime("%Y-%m-%d")
        description = " ".join(description_parts) if description_parts else None

        data = {
            "amount": amount,
            "category": category,
            "description": description,
            "transaction_date": date
        }
        
        response = requests.post(f"{API_URL}/transactions/", json=data)
        await update.message.reply_text(f"✅ Трата {amount}₽ на {category} сохранена! Дата: {date}")
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
        for tr in transactions:
            tr_date = datetime.strptime(tr['date'], "%Y-%m-%d").strftime("%d.%m.%Y")
            message += (
                f"Id {tr['id']}\n"
                f"Сумма {tr['amount']} ₽ - {tr['category']}\n"
                f"Комментария {tr.get('description', 'нет описания')}\n"
                f"Дата {tr_date}\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении трат: {str(e)}")

async def delete_transaction(update: Update, context):
    try:
        args = update.message.text.split()
        if len(args) < 2:
            await update.message.reply_text("❌ Формат: /delete <id транзакции>")
            return

        transaction_id = args[1]
        response = requests.delete(f"{API_URL}/transactions/{transaction_id}")
        
        if response.status_code == 200:
            await update.message.reply_text("✅ Трата успешно удалена")
        else:
            await update.message.reply_text("❌ Не удалось удалить трату. Проверьте ID")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_transaction))
    app.add_handler(CommandHandler("list", list_transactions))
    app.add_handler(CommandHandler("delete", delete_transaction))
    
    app.run_polling()

if __name__ == "__main__":
    run_bot()