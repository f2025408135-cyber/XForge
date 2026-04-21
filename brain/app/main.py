from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="XForge Brain API", description="Autonomous Offensive Security Intelligence Layer")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Allow all origins for the dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("XForge Brain initializing...")
    from .result_consumer import run_consumer_in_background
    run_consumer_in_background()

@app.get("/")
def read_root():
    return {"status": "XForge Brain is operational"}

@app.post("/targets/", response_model=schemas.Target)
def create_target(target: schemas.TargetCreate, db: Session = Depends(get_db)):
    db_target = db.query(models.Target).filter(models.Target.domain == target.domain).first()
    if db_target:
        raise HTTPException(status_code=400, detail="Target domain already registered")
    
    new_target = models.Target(domain=target.domain)
    db.add(new_target)
    db.commit()
    db.refresh(new_target)
    return new_target

@app.get("/targets/", response_model=List[schemas.Target])
def read_targets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    targets = db.query(models.Target).offset(skip).limit(limit).all()
    return targets

@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # Verify target exists
    db_target = db.query(models.Target).filter(models.Target.id == task.target_id).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
        
    new_task = models.Task(target_id=task.target_id, attack_type=task.attack_type)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # Push task schema payload to RabbitMQ for Executor to pick up
    from .queue import publish_task
    import uuid
    
    payload = {
        "task_id": f"task-{new_task.id}-{uuid.uuid4().hex[:8]}",
        "target_url": f"https://{db_target.domain}",
        "attack_type": new_task.attack_type,
        "payloads": [] # Populated later by the Theorist Agent
    }
    publish_task(payload)
    
    return new_task

@app.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Task).offset(skip).limit(limit).all()

@app.get("/reports/{target_id}")
def generate_report(target_id: int, db: Session = Depends(get_db)):
    from .reporter import ReportGenerator
    reporter = ReportGenerator(db)
    report_md = reporter.generate_markdown_report(target_id)
    
    if "Error: Target not found." in report_md:
        raise HTTPException(status_code=404, detail="Target not found")
        
    return {"target_id": target_id, "markdown_report": report_md}

@app.get("/targets/{target_id}/scope")
def get_target_scope(target_id: int, db: Session = Depends(get_db)):
    target = db.query(models.Target).filter(models.Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    nodes = [{"id": f"target_{target.id}", "name": target.domain, "group": 1, "val": 20}]
    links = []

    subdomains = db.query(models.Subdomain).filter(models.Subdomain.target_id == target_id).all()
    for sub in subdomains:
        sub_node_id = f"sub_{sub.id}"
        nodes.append({"id": sub_node_id, "name": sub.hostname, "group": 2, "val": 10})
        links.append({"source": f"target_{target.id}", "target": sub_node_id})

        ports = db.query(models.Port).filter(models.Port.subdomain_id == sub.id).all()
        for p in ports:
            port_node_id = f"port_{p.id}"
            nodes.append({"id": port_node_id, "name": f"Port {p.port_number}", "group": 3, "val": 5})
            links.append({"source": sub_node_id, "target": port_node_id})

    return {"nodes": nodes, "links": links}

@app.post("/scan/full/{domain}")
def trigger_full_scan(domain: str, db: Session = Depends(get_db)):
    from .coordinator import MasterCoordinator
    
    # We strip any protocols for normalization
    clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
    
    coordinator = MasterCoordinator(db)
    result = coordinator.initiate_full_scan(clean_domain)
    
    return result
