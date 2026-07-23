import pytest
import asyncio
from app.database import SessionLocal, engine
from app.models import Base, Target, Task, Subdomain, Port, Vulnerability, Finding
from app.reporter import ReportGenerator
import uuid

@pytest.mark.asyncio
async def test_full_system_simulation():
    # Simulate the DB state after a full scan has completed successfully
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Try to clean up target if exists from a previous bad run
    existing_t = db.query(Target).filter(Target.domain=="hackerone.com").first()
    if existing_t:
        db.delete(existing_t)
        db.commit()

    # 1. Target Created
    t = Target(domain="hackerone.com")
    db.add(t)
    db.commit()
    db.refresh(t)
    
    # 2. Recon Ingested
    sub1 = Subdomain(target_id=t.id, hostname="api.hackerone.com", ip_address="104.16.99.52")
    sub2 = Subdomain(target_id=t.id, hostname="docs.hackerone.com", ip_address="104.16.100.52")
    db.add_all([sub1, sub2])
    db.commit()
    db.refresh(sub1)
    db.refresh(sub2)
    
    p1 = Port(subdomain_id=sub1.id, port_number=443, service="https")
    p2 = Port(subdomain_id=sub1.id, port_number=80, service="http")
    p3 = Port(subdomain_id=sub2.id, port_number=443, service="https")
    db.add_all([p1, p2, p3])
    
    v1 = Vulnerability(
        subdomain_id=sub1.id, 
        template_id="cve-2021-44228", 
        severity="critical", 
        description="Apache Log4j2 RCE", 
        matched_at="https://api.hackerone.com/graphql"
    )
    v2 = Vulnerability(
        subdomain_id=sub2.id, 
        template_id="tech-detect", 
        severity="info", 
        description="Wappalyzer Technology Detection", 
        matched_at="https://docs.hackerone.com"
    )
    db.add_all([v1, v2])
    
    # 3. Fuzzing Tasks Executed & Evaluated
    task_bola = Task(target_id=t.id, attack_type="bola", status="COMPLETED")
    task_race = Task(target_id=t.id, attack_type="race_condition", status="COMPLETED")
    db.add_all([task_bola, task_race])
    db.commit()
    db.refresh(task_bola)
    db.refresh(task_race)
    
    find_bola = Finding(
        task_id=task_bola.id, 
        score=90, 
        description="High confidence BOLA on /api/users/999: Non-admin role achieved 200 with similar payload size to admin.",
        raw_evidence="curl -X GET 'https://api.hackerone.com/api/users/999' -H 'Authorization: Bearer standard'"
    )
    find_race = Finding(
        task_id=task_race.id, 
        score=100, 
        description="Race Condition Verified: 5 concurrent requests successfully bypassed limit check.",
        raw_evidence="curl -X POST 'https://api.hackerone.com/api/redeem' -H 'Authorization: Bearer test' -d '{\"code\": \"123\"}'"
    )
    db.add_all([find_bola, find_race])
    db.commit()
    
    # 4. Generate Report
    reporter = ReportGenerator(db)
    report_md = reporter.generate_markdown_report(t.id)
    
    with open("demo_report.md", "w") as f:
        f.write(report_md)
        
    assert "XForge Autonomous Security Report: hackerone.com" in report_md
    assert "Apache Log4j2 RCE" in report_md
    assert "High confidence BOLA" in report_md
    assert "Race Condition Verified" in report_md
    
    # Cleanup for next tests
    db.delete(t)
    db.commit()
    db.close()
