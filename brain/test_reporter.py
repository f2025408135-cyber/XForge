import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Target, Subdomain, Port, Vulnerability, Task, Finding
from app.reporter import ReportGenerator

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

def test_generate_markdown_report_full(db_session):
    # Seed Database
    t = Target(domain="tesla.com")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    
    sub = Subdomain(target_id=t.id, hostname="api.tesla.com", ip_address="1.1.1.1")
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)
    
    p = Port(subdomain_id=sub.id, port_number=443, service="https")
    v = Vulnerability(subdomain_id=sub.id, template_id="cve-2021-1234", severity="high", description="Test CVE", matched_at="https://api.tesla.com")
    db_session.add_all([p, v])
    
    tsk = Task(target_id=t.id, attack_type="bola", status="COMPLETED")
    db_session.add(tsk)
    db_session.commit()
    db_session.refresh(tsk)
    
    fnd = Finding(task_id=tsk.id, score=1, description="High Confidence BOLA", raw_evidence="curl -X GET 'https://api.tesla.com'")
    db_session.add(fnd)
    db_session.commit()

    # Generate Report
    reporter = ReportGenerator(db_session)
    report = reporter.generate_markdown_report(t.id)
    
    # Assertions
    assert "XForge Autonomous Security Report: tesla.com" in report
    assert "api.tesla.com (1.1.1.1)" in report
    assert "**Open Ports:** 443" in report
    assert "[HIGH] cve-2021-1234: Test CVE" in report
    assert "BOLA Vulnerability Detected" in report
    assert "High Confidence BOLA" in report
    assert "curl -X GET 'https://api.tesla.com'" in report

def test_generate_markdown_report_empty(db_session):
    # Missing Target
    reporter = ReportGenerator(db_session)
    report = reporter.generate_markdown_report(999)
    assert report == "Error: Target not found."
    
    # Target with no data
    t = Target(domain="empty.com")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    
    report2 = reporter.generate_markdown_report(t.id)
    assert "empty.com" in report2
    assert "No subdomains discovered." in report2
    assert "No active exploitation anomalies detected" in report2
