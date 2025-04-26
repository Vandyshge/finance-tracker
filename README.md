# 📊 Financial Tracker with FastAPI 
<!-- & Telegram Bot   -->

Простой трекер расходов с REST API (FastAPI)
 <!-- и Telegram-ботом для удобного добавления трат.   -->

## 🚀 **Features**  
- Добавление транзакций через:  
  <!-- - **Telegram-бота** (`/add 500 еда обед`)   -->
  - **REST API** (Swagger UI, cURL)  
- Просмотр истории трат  
- SQLite база данных (можно переключить на PostgreSQL)  
- Автоматическое создание таблиц при запуске  

## ⚙️ **Installation**  

```bash
git clone https://github.com/yourusername/finance-tracker.git
cd finance-tracker
pip install -r requirements.txt
uvicorn app.main:app --reload
