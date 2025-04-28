from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas, auth, dependencies
from .database import get_db, engine
from datetime import timedelta

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

# AUTH
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"status": "success", "user_id": db_user.id}

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(user: models.User = Depends(dependencies.get_current_user_from_bearer)):
    return {"message": "Authenticated!"}

@app.get("/users/me", response_model=schemas.UserInDB)
def read_users_me(current_user: models.User = Depends(dependencies.get_current_user_from_bearer)):
    return current_user

@app.get("/user_by_email/{email}")
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username}

# TRANSACTIONS
@app.post("/transactions/", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, current_user: models.User = Depends(dependencies.get_current_user_from_bearer), db: Session = Depends(get_db)):
    db_transaction = models.Transaction(
        amount=transaction.amount,
        description=transaction.description,
        date=transaction.date,
        owner_id=current_user.id,
        category_id=transaction.category_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/transactions/", response_model=list[schemas.TransactionResponse])
def list_transactions(current_user: models.User = Depends(dependencies.get_current_user_from_bearer), db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).order_by(desc(models.Transaction.date)).all()
    return transactions

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, current_user: models.User = Depends(dependencies.get_current_user_from_bearer), db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id, models.Transaction.owner_id == current_user.id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(transaction)
    db.commit()
    return {"status": "Transaction deleted"}

# CATEGORIES
@app.post("/categories/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, current_user: models.User = Depends(dependencies.get_current_user_from_bearer), db: Session = Depends(get_db)):
    db_category = models.Category(name=category.name, owner_id=current_user.id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories/", response_model=list[schemas.CategoryResponse])
def list_categories(current_user: models.User = Depends(dependencies.get_current_user_from_bearer), db: Session = Depends(get_db)):
    categories = db.query(models.Category).filter(models.Category.owner_id == current_user.id).all()
    return categories

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, current_user: models.User = Depends(dependencies.get_current_user_from_bearer), db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id, models.Category.owner_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"status": "Category deleted"}
