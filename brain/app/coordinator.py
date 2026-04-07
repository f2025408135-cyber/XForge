from sqlalchemy.orm import Session
from .models import Target, Task
from .queue import publish_task
import uuid

class MasterCoordinator:
    """
    The orchestrator of the entire autonomous workflow.
    Schedules and dispatches the initial OSS Recon tasks (Subfinder, Naabu, Nuclei),
    then orchestrates the AI-driven Theorist payload generation (BOLA, Race, SQLi).
    """
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_target(self, domain: str) -> Target:
        target = self.db.query(Target).filter(Target.domain == domain).first()
        if not target:
            target = Target(domain=domain)
            self.db.add(target)
            self.db.commit()
            self.db.refresh(target)
        return target

    def dispatch_task(self, target: Target, attack_type: str, payloads: list = None) -> Task:
        # 1. Create Task in DB
        task = Task(target_id=target.id, attack_type=attack_type, status="PENDING")
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # 2. Publish to RabbitMQ
        payload = {
            "task_id": f"task-{task.id}-{uuid.uuid4().hex[:8]}",
            "target_url": f"https://{target.domain}",
            "attack_type": attack_type,
            "payloads": payloads or []
        }
        
        success = publish_task(payload)
        if not success:
            task.status = "FAILED_TO_QUEUE"
            self.db.commit()
            
        return task

    def initiate_full_scan(self, domain: str) -> dict:
        """
        Orchestrates the entire attack lifecycle for a domain.
        """
        target = self.get_or_create_target(domain)
        dispatched_tasks = []

        # --- Phase 1: OSS Reconnaissance ---
        # The Executor Go wrappers will handle the binaries and drop the JSON back for the ReconParser
        subfinder_task = self.dispatch_task(target, "subfinder_scan")
        dispatched_tasks.append(subfinder_task.id)

        naabu_task = self.dispatch_task(target, "naabu_scan")
        dispatched_tasks.append(naabu_task.id)

        nuclei_task = self.dispatch_task(target, "nuclei_scan")
        dispatched_tasks.append(nuclei_task.id)

        # --- Phase 2: Autonomous Fuzzing (Logic, BOLA, Race, Injection) ---
        # In a fully asynchronous environment, this phase would trigger only after Phase 1 completes
        # and the OpenAPI spec is discovered. For the API response, we will trigger placeholder 
        # tasks that the Executor/Brain loop will dynamically populate.
        
        bola_task = self.dispatch_task(target, "bola")
        dispatched_tasks.append(bola_task.id)
        
        race_task = self.dispatch_task(target, "race_condition")
        dispatched_tasks.append(race_task.id)
        
        inj_task = self.dispatch_task(target, "injection")
        dispatched_tasks.append(inj_task.id)
        
        logic_task = self.dispatch_task(target, "logic_abuse")
        dispatched_tasks.append(logic_task.id)

        return {
            "status": "Scan Initiated",
            "target_id": target.id,
            "domain": target.domain,
            "tasks_dispatched": len(dispatched_tasks),
            "task_ids": dispatched_tasks
        }
