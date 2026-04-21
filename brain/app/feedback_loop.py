import json
import logging
from typing import Dict, List
from .evaluator import EvaluatorAgent
from .theorist import TheoristAgent
from .memory import PayloadMemory
from .models import Task
from .queue import publish_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FeedbackLoop:
    """
    Implements the self-healing intelligence loop.
    If a payload is blocked by a WAF (403) or fails, the Evaluator feeds the failure 
    back to the Theorist. The Theorist queries ChromaDB for memory of past successful 
    bypasses, mutates the payload, and queues a new iteration of the task.
    """
    
    MAX_ITERATIONS = 5

    def __init__(self, db: Session):
        self.db = db
        self.evaluator = EvaluatorAgent()
        self.theorist = TheoristAgent()
        self.memory = PayloadMemory()

    async def process_fuzz_result(self, task: Task, results: List[Dict], target_url: str):
        """
        Receives raw HTTP responses. If a WAF block is detected (e.g. 403), 
        triggers the feedback loop up to MAX_ITERATIONS.
        """
        # 1. Base Evaluation
        eval_report = {"vuln_score": 0, "findings": []}
        
        if task.attack_type == "bola":
            eval_report = self.evaluator.evaluate_bola(results)
        elif task.attack_type in ["logic_abuse", "race_condition", "injection"]:
            # Basic fallback for demo purposes
            eval_report = {"vuln_score": 0.5, "findings": ["Potential anomaly flagged."]}

        # If we succeeded, store it in Vector Memory!
        if eval_report.get("vuln_score", 0) > 0:
            for r in results:
                if r.get("StatusCode") in [200, 201]:
                    payload_json = json.dumps({"method": r.get("Method"), "path": r.get("Path")})
                    self.memory.store_success(
                        task_id=f"T{task.id}",
                        attack_type=task.attack_type,
                        payload_json=payload_json,
                        description=f"Successful execution against {task.attack_type}"
                    )
            return eval_report, True # Success

        # 2. Failure Detection (e.g., Blocked by WAF)
        blocked = any(r.get("StatusCode") == 403 for r in results)
        
        # We store iteration count in the Task model status field temporarily as PENDING-1, PENDING-2, etc.
        iteration = 1
        if "-" in task.status:
            try:
                iteration = int(task.status.split("-")[1])
            except ValueError:
                pass
                
        if blocked and iteration < self.MAX_ITERATIONS:
            logger.info(f"WAF Block detected for task {task.id}. Triggering feedback loop iteration {iteration + 1}...")
            
            # Query ChromaDB for successful bypasses
            past_successes = self.memory.retrieve_similar_payloads(
                attack_type=task.attack_type,
                context=f"Bypass 403 Forbidden for {task.attack_type}",
                n_results=1
            )
            
            memory_context = ""
            if past_successes:
                memory_context = f"Here is a payload that worked previously: {past_successes}"

            # Rewrite Payload via Theorist LLM (In real system, we'd pass raw failed payloads back)
            system_prompt = f"""
You are an AI evasion agent. A recent {task.attack_type} payload was blocked by a WAF (403).
{memory_context}

Rewrite the JSON payload to evade the WAF (e.g., using alternative encoding, method swapping, HTTP parameter pollution).
Return ONLY the raw JSON array matching:
[
  {{ "method": "GET", "path": "/api/v1", "headers": {{}}, "body": "" }}
]
"""
            try:
                import os
                import uuid
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy_key"))
                
                response = await client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "system", "content": system_prompt}],
                    response_format={ "type": "json_object" },
                    temperature=0.8
                )
                
                content = response.choices[0].message.content
                # Robust parsing handling Markdown formatting or trailing characters
                content = content.strip().strip('`')
                if content.lower().startswith('json\n'):
                    content = content[5:]
                if content.lower().startswith('json'):
                    content = content[4:]

                new_payloads = json.loads(content).get("payloads", [])

                if new_payloads:
                    # Update iteration counter
                    task.status = f"PENDING-{iteration + 1}"
                    self.db.commit()
                    
                    # Re-queue
                    queue_payload = {
                        "task_id": f"task-{task.id}-{uuid.uuid4().hex[:8]}",
                        "target_url": target_url,
                        "attack_type": task.attack_type,
                        "payloads": new_payloads
                    }
                    publish_task(queue_payload)
                    return eval_report, False # Returned to queue
            except Exception as e:
                logger.error(f"Feedback loop LLM rewrite failed: {e}")

        # If it wasn't blocked, or we hit max iterations, complete it.
        task.status = "COMPLETED"
        self.db.commit()
        return eval_report, True
