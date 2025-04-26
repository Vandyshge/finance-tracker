from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from pydantic import BaseModel
from datetime import date
from typing import Optional

app = FastAPI()

# Создаем таблицы
models.Base.metadata.create_all(bind=database.engine)

# Исправленная модель Pydantic
class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    transaction_date: date = date.today()  # Изменили имя поля с date на transaction_date
    
    class Config:
        from_attributes = True

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/transactions/")
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = models.Transaction(
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        date=transaction.transaction_date,
        user_id=1  # Временное значение для теста
    )
    db.add(db_transaction)
    db.commit()
    return {"status": "Transaction added"}

@app.get("/transactions/")
def read_transactions(db: Session = Depends(get_db)):
    return db.query(models.Transaction).all()