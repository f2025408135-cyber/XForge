import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Target, Subdomain, Port, Vulnerability
from app.recon_parser import ReconParser

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

@pytest.fixture(scope="function")
def setup_target(db_session):
    target = Target(domain="example.com")
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target

def test_ingest_subfinder(db_session, setup_target):
    parser = ReconParser(db=db_session, target_id=setup_target.id)
    mock_data = [
        {"host": "api.example.com", "source": "certspotter"},
        {"host": "dev.example.com", "source": "crtsh"}
    ]
    
    parser.ingest_subfinder(mock_data)
    
    subdomains = db_session.query(Subdomain).filter_by(target_id=setup_target.id).all()
    assert len(subdomains) == 2
    assert subdomains[0].hostname == "api.example.com"
    assert subdomains[1].hostname == "dev.example.com"

def test_ingest_naabu(db_session, setup_target):
    parser = ReconParser(db=db_session, target_id=setup_target.id)
    mock_data = [
        {"host": "api.example.com", "ip": "1.2.3.4", "port": 80},
        {"host": "api.example.com", "ip": "1.2.3.4", "port": 443}
    ]
    
    parser.ingest_naabu(mock_data)
    
    subdomain = db_session.query(Subdomain).filter_by(hostname="api.example.com").first()
    assert subdomain is not None
    assert subdomain.ip_address == "1.2.3.4"
    
    ports = db_session.query(Port).filter_by(subdomain_id=subdomain.id).all()
    assert len(ports) == 2
    assert ports[0].port_number == 80
    assert ports[1].port_number == 443

def test_ingest_nuclei(db_session, setup_target):
    parser = ReconParser(db=db_session, target_id=setup_target.id)
    mock_data = [
        {
            "template-id": "cve-2021-44228",
            "info": {
                "name": "Apache Log4j2 Remote Code Execution",
                "severity": "critical"
            },
            "host": "https://api.example.com",
            "matched-at": "https://api.example.com/?q=test"
        }
    ]
    
    parser.ingest_nuclei(mock_data)
    
    vulns = db_session.query(Vulnerability).all()
    assert len(vulns) == 1
    assert vulns[0].template_id == "cve-2021-44228"
    assert vulns[0].severity == "critical"
    
    sub = db_session.query(Subdomain).filter_by(id=vulns[0].subdomain_id).first()
    assert sub.hostname == "api.example.com"
