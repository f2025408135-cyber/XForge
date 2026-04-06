import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.database import Base

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_xforge.db"

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

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup: clean db before test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    Base.metadata.drop_all(bind=engine)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "XForge Brain is operational"}

def test_create_target():
    response = client.post(
        "/targets/",
        json={"domain": "example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "example.com"
    assert "id" in data
    
def test_create_target_duplicate():
    client.post("/targets/", json={"domain": "example.com"})
    response = client.post("/targets/", json={"domain": "example.com"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Target domain already registered"

def test_create_task():
    # Create target first
    target_resp = client.post("/targets/", json={"domain": "test.com"})
    target_id = target_resp.json()["id"]
    
    response = client.post(
        "/tasks/",
        json={"target_id": target_id, "attack_type": "bola"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["attack_type"] == "bola"
    assert data["status"] == "PENDING"
    
def test_create_task_invalid_target():
    response = client.post(
        "/tasks/",
        json={"target_id": 999, "attack_type": "bola"},
    )
    assert response.status_code == 404
