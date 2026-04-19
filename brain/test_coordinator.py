import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Target, Task
from app.coordinator import MasterCoordinator

# Setup DB
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_get_or_create_target(db_session):
    coord = MasterCoordinator(db_session)
    
    # Create new target
    t1 = coord.get_or_create_target("hackerone.com")
    assert t1.id is not None
    assert t1.domain == "hackerone.com"
    
    # Retrieve existing target
    t2 = coord.get_or_create_target("hackerone.com")
    assert t1.id == t2.id

def test_initiate_full_scan(mocker, db_session):
    # Mock the rabbitmq publisher to prevent network errors in test
    mock_publish = mocker.patch('app.coordinator.publish_task', return_value=True)
    
    coord = MasterCoordinator(db_session)
    result = coord.initiate_full_scan("bugcrowd.com")
    
    assert result["status"] == "Scan Initiated"
    assert result["domain"] == "bugcrowd.com"
    assert result["tasks_dispatched"] == 8
    assert len(result["task_ids"]) == 8
    
    # Check DB Population
    tasks = db_session.query(Task).all()
    assert len(tasks) == 8
    
    attack_types = [t.attack_type for t in tasks]
    assert "subfinder_scan" in attack_types
    assert "nuclei_scan" in attack_types
    assert "bola" in attack_types
    assert "race_condition" in attack_types
    assert "injection" in attack_types
    assert "logic_abuse" in attack_types
    
    # Check queue publishing was called for each task
    assert mock_publish.call_count == 8
