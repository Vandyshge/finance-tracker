from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import requests
from datetime import datetime

API_URL = "http://localhost:8001"
TOKEN = "7879703019:AAHgq3YSlU4wug2L0vC5aSf57XX5MvFfO_U"

# Состояния для регистрации
REGISTER, EMAIL, PASSWORD = range(3)
# Состояния для входа
LOGIN_EMAIL, LOGIN_PASSWORD = range(3, 5)

async def start(update: Update, context):
    await update.message.reply_text(
        "💰 Финансовый трекер\n\n"
        "Доступные команды:\n"
        "/register - зарегистрироваться\n"
        "/login - войти в систему\n"
        "/logout - выйти из системы\n"
        "/add <сумма> <категория> [описание] [дата] - добавить трату\n"
        "/list - показать все траты\n"
        "/delete <id> - удалить трату\n"
    )

async def register(update: Update, context):
    await update.message.reply_text(
        "📝 Регистрация\n\n"
        "Введите ваш email:"
    )
    return EMAIL

async def get_email(update: Update, context):
    try:
        context.user_data['email'] = update.message.text
        await update.message.reply_text("Придумайте пароль:")
        return PASSWORD
    except Exception as e:
        print("Error in get_email:", str(e))
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

async def get_password(update: Update, context):
    context.user_data['password'] = update.message.text
    email = context.user_data['email']
    password = context.user_data['password']
    user_id = str(update.message.from_user.id)  # Используем ID Telegram как username
    
    try:
        # Регистрация
        response = requests.post(
            f"{API_URL}/register",
            json={
                "email": email,
                "username": user_id,  # Используем user_id как username
                "password": password
            }
        )
        
        if response.status_code >= 400:
            error = response.json().get("detail", "Registration failed")
            await update.message.reply_text(f"❌ Ошибка: {error}")
            return ConversationHandler.END
        
        # Автоматический вход после регистрации
        auth_response = requests.post(
            f"{API_URL}/token",
            data={
                "username": user_id,  # Используем user_id для входа
                "password": password
            }
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            context.user_data['token'] = token
            await update.message.reply_text("✅ Регистрация и вход выполнены!")
        else:
            await update.message.reply_text(f"✅ Регистрация успешна, но вход не выполнен. Ошибка: {auth_response.text}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def login(update: Update, context):
    await update.message.reply_text("🔑 Вход в систему\n\nВведите ваш email:")
    return LOGIN_EMAIL

async def login_email(update: Update, context):
    context.user_data['login_email'] = update.message.text
    await update.message.reply_text("Введите ваш пароль:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context):
    password = update.message.text
    email = context.user_data['login_email']
    user_id = str(update.message.from_user.id)  # Получаем user_id из Telegram
    
    try:
        # Получаем username (user_id) по email
        user_info = requests.get(f"{API_URL}/user_by_email/{email}")
        if user_info.status_code != 200:
            await update.message.reply_text("❌ Пользователь с таким email не найден")
            return ConversationHandler.END
            
        username = user_info.json().get("username")
        
        # Авторизация
        auth_response = requests.post(
            f"{API_URL}/token",
            data={
                "username": username,  # Используем username (user_id)
                "password": password
            }
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()["access_token"]
            context.user_data['token'] = token
            await update.message.reply_text("✅ Вход выполнен успешно!")
        else:
            await update.message.reply_text("❌ Неверный пароль")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def logout(update: Update, context):
    if 'token' in context.user_data:
        del context.user_data['token']
        await update.message.reply_text("✅ Вы вышли из системы")
    else:
        await update.message.reply_text("❌ Вы не вошли в систему")

async def cancel(update: Update, context):
    await update.message.reply_text("Операция отменена")
    return ConversationHandler.END

async def add_transaction(update: Update, context):
    if 'token' not in context.user_data:
        await update.message.reply_text("❌ Сначала выполните вход (/login)")
        return
    
    try:
        args = update.message.text.split()
        if len(args) < 3:
            await update.message.reply_text("❌ Формат: /add <сумма> <категория> [описание] [дата в формате ДД.ММ.ГГГГ]")
            return

        amount = float(args[1])
        category = args[2]
        
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
            "date": date
        }
        
        response = requests.post(
            f"{API_URL}/transactions/",
            json=data,
            headers={"Authorization": f"Bearer {context.user_data['token']}"}
        )
        
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Трата {amount}₽ на {category} сохранена! Дата: {date}")
        else:
            await update.message.reply_text(f"❌ Ошибка: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def list_transactions(update: Update, context):
    if 'token' not in context.user_data:
        await update.message.reply_text("❌ Сначала выполните вход (/login)")
        return
    
    try:
        response = requests.get(
            f"{API_URL}/transactions/",
            headers={"Authorization": f"Bearer {context.user_data.get('token', '')}"}
        )
        
        if response.status_code != 200:
            await update.message.reply_text(f"❌ Ошибка сервера: {response.text}")
            return
            
        transactions = response.json()
        
        if not transactions:
            await update.message.reply_text("📭 Список трат пуст")
            return
            
        message = "📋 История трат (новые сверху):\n\n"
        for tr in transactions:
            # Проверяем разные возможные форматы даты
            tr_date = tr.get('date') or tr.get('transaction_date')
            if isinstance(tr_date, str):
                try:
                    tr_date = datetime.strptime(tr_date, "%Y-%m-%d").strftime("%d.%m.%Y")
                except ValueError:
                    tr_date = tr_date  # Оставляем как есть, если не удалось распарсить
            
            message += (
                f"🆔 {tr.get('id', 'N/A')}\n"
                f"📅 {tr_date}\n"
                f"💰 {tr.get('amount', 0)} ₽ - {tr.get('category', 'без категории')}\n"
                f"👤 Владелец: {tr.get('owner_id', tr.get('user_id', 'N/A'))}\n"
                f"📝 {tr.get('description', 'нет описания')}\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def delete_transaction(update: Update, context):
    if 'token' not in context.user_data:
        await update.message.reply_text("❌ Сначала выполните вход (/login)")
        return

    try:
        args = update.message.text.split()
        if len(args) < 2:
            await update.message.reply_text("❌ Формат: /delete <id транзакции>")
            return

        transaction_id = args[1]
        response = requests.delete(
            f"{API_URL}/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {context.user_data['token']}"}
        )
        
        if response.status_code == 200:
            await update.message.reply_text("✅ Трата успешно удалена")
        else:
            await update.message.reply_text(f"❌ Не удалось удалить трату. Ошибка: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('register', register),
            CommandHandler('login', login)
        ],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("add", add_transaction))
    app.add_handler(CommandHandler("list", list_transactions))
    app.add_handler(CommandHandler("delete", delete_transaction))
    
    app.run_polling()

if __name__ == "__main__":
    run_bot()