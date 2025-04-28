import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from jose import jwt

from .main import app
from .database import Base, get_db
from . import models, auth

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass"
    }

@pytest.fixture
def test_category():
    return {
        "name": "Food"
    }

@pytest.fixture
def test_transaction():
    return {
        "amount": 100.50,
        "description": "Lunch",
        "date": str(date.today()),
        "category_id": 1
    }

def create_test_user(db, user_data):
    hashed_password = auth.get_password_hash(user_data["password"])
    db_user = models.User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_test_category(db, user_id, category_data):
    db_category = models.Category(
        name=category_data["name"],
        owner_id=user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def create_test_transaction(db, user_id, transaction_data):
    db_transaction = models.Transaction(
        amount=transaction_data["amount"],
        description=transaction_data["description"],
        date=transaction_data["date"],
        owner_id=user_id,
        category_id=transaction_data["category_id"]
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_auth_token(username):
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return access_token

def test_register_user(test_user):
    db = TestingSessionLocal()
    db.query(models.User).filter(models.User.email == test_user["email"]).delete()
    db.commit()
    
    response = client.post("/register", json=test_user)
    assert response.status_code == 200
    assert "user_id" in response.json()
    
    response = client.post("/register", json=test_user)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login(test_user):
    db = TestingSessionLocal()
    create_test_user(db, test_user)
    
    response = client.post("/token", data={
        "username": test_user["username"],
        "password": "wrongpass"
    })
    assert response.status_code == 401
    
    response = client.post("/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_protected_route(test_user):
    token = get_auth_token(test_user["username"])
    
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Authenticated!"}
    
    response = client.get("/protected", headers={"Authorization": "Bearer wrongtoken"})
    assert response.status_code == 401

def test_get_current_user(test_user):
    token = get_auth_token(test_user["username"])
    
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == test_user["username"]
    assert response.json()["email"] == test_user["email"]

def test_create_category(test_user, test_category):
    db = TestingSessionLocal()
    user = create_test_user(db, test_user)
    token = get_auth_token(test_user["username"])
    
    response = client.post(
        "/categories/",
        json=test_category,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == test_category["name"]
    assert response.json()["owner_id"] == user.id

def test_list_categories(test_user, test_category):
    db = TestingSessionLocal()
    user = create_test_user(db, test_user)
    create_test_category(db, user.id, test_category)
    token = get_auth_token(test_user["username"])
    
    response = client.get(
        "/categories/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == test_category["name"]

def test_delete_category(test_user, test_category):
    db = TestingSessionLocal()
    user = create_test_user(db, test_user)
    category = create_test_category(db, user.id, test_category)
    token = get_auth_token(test_user["username"])
    
    response = client.delete(
        f"/categories/{category.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Category deleted"
    
    response = client.get(
        "/categories/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(response.json()) == 0

def test_create_transaction(test_user, test_category, test_transaction):
    db = TestingSessionLocal()
    user = create_test_user(db, test_user)
    category = create_test_category(db, user.id, test_category)
    token = get_auth_token(test_user["username"])
    
    test_transaction["category_id"] = category.id
    response = client.post(
        "/transactions/",
        json=test_transaction,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["amount"] == test_transaction["amount"]
    assert response.json()["description"] == test_transaction["description"]
    assert response.json()["owner_id"] == user.id

def test_list_transactions(test_user, test_category, test_transaction):
    db = TestingSessionLocal()
    user = create_test_user(db, test_user)
    category = create_test_category(db, user.id, test_category)
    test_transaction["category_id"] = category.id
    create_test_transaction(db, user.id, test_transaction)
    token = get_auth_token(test_user["username"])
    
    response = client.get(
        "/transactions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["amount"] == test_transaction["amount"]

def test_delete_transaction(test_user, test_category, test_transaction):
    db = TestingSessionLocal()
    user = create_test_user(db, test_user)
    category = create_test_category(db, user.id, test_category)
    test_transaction["category_id"] = category.id
    transaction = create_test_transaction(db, user.id, test_transaction)
    token = get_auth_token(test_user["username"])
    
    response = client.delete(
        f"/transactions/{transaction.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Transaction deleted"
    
    response = client.get(
        "/transactions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(response.json()) == 0

def test_get_user_by_email(test_user):
    db = TestingSessionLocal()
    create_test_user(db, test_user)
    
    response = client.get(f"/user_by_email/{test_user['email']}")
    assert response.status_code == 200
    assert response.json()["username"] == test_user["username"]
    
    response = client.get("/user_by_email/nonexistent@example.com")
    assert response.status_code == 404