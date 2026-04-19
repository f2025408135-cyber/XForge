import pika
import json
import os
import threading
import time

from app.database import SessionLocal
from app.models import Task, Finding
from app.evaluator import EvaluatorAgent
from app.feedback_loop import FeedbackLoop
from app.poc_generator import PoCGenerator
from app.recon_parser import ReconParser

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://xforge:xforge_password@localhost:5672/")

class ResultConsumer:
    """
    Listens continuously on the RabbitMQ `fuzz_results` queue for JSON payloads 
    sent back by the Go Executor. When received, it triggers the Evaluator Agent
    to score anomalies and updates the database with actionable Vulnerability Findings.
    """
    def __init__(self):
        self.evaluator = EvaluatorAgent()

    def callback(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            task_id_str = data.get("task_id", "")
            
            # task_id format is "task-{DB_ID}-{UUID}"
            try:
                db_task_id = int(task_id_str.split("-")[1])
            except (IndexError, ValueError):
                print(f"Failed to parse DB Task ID from {task_id_str}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            print(f" [✓] Received fuzzing results for Task ID {db_task_id} ({data.get('attack_type')})")
            
            # Spin up a database session for this message
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == db_task_id).first()
                if not task:
                    print(f"Task {db_task_id} not found in DB.")
                    return

                results = data.get("results", [])
                
                attack_type = data.get("attack_type")
                
                # --- Phase 1: Reconnaissance Ingestion ---
                if attack_type in ["subfinder_scan", "naabu_scan", "nuclei_scan"]:
                    parser = ReconParser(db, task.target_id)
                    
                    # We stored the raw JSON bytes in the 'Error' field of FuzzResult in Go for simplicity
                    for res in results:
                        raw_json_str = res.get("Error", "[]")
                        try:
                            parsed_json = json.loads(raw_json_str)
                            if attack_type == "subfinder_scan":
                                parser.ingest_subfinder(parsed_json)
                            elif attack_type == "naabu_scan":
                                parser.ingest_naabu(parsed_json)
                            elif attack_type == "nuclei_scan":
                                parser.ingest_nuclei(parsed_json)
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON for {attack_type} result.")

                    task.status = "COMPLETED"
                    db.commit()
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # --- Phase 2: Vulnerability Evaluation & Feedback Loop ---
                import asyncio
                from app.feedback_loop import FeedbackLoop
                
                feedback_agent = FeedbackLoop(db)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    eval_report, is_complete = loop.run_until_complete(
                        feedback_agent.process_fuzz_result(task, results, data.get("target_url"))
                    )
                    
                    # If it was requeued by the feedback loop, skip reporting
                    if not is_complete:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return
                    
                    # If the evaluator found something, store it as a Finding
                    if eval_report.get("vuln_score", 0) > 0:
                        for description in eval_report.get("findings", []):
                            raw_poc = ""
                            if results:
                                p = results[0]
                                bundle = PoCGenerator.create_poc_bundle(
                                    method=p.get("Method", "GET"),
                                    target_url=data.get("target_url"),
                                    path=p.get("Path", "/"),
                                    headers={"Authorization": "Bearer injected"}, 
                                    body=p.get("Body", "")
                                )
                                raw_poc = bundle["curl"]

                            finding = Finding(
                                task_id=task.id,
                                score=int(eval_report.get("vuln_score", 0) * 100),
                                description=description,
                                raw_evidence=raw_poc
                            )
                            db.add(finding)
                    
                    db.commit()
                finally:
                    loop.close()

            finally:
                db.close()
            
            # Acknowledge completion back to RabbitMQ
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error processing result queue message: {e}")
            # Reject message but do not requeue to prevent poison loops
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue='fuzz_results', durable=True)
            
            channel.basic_consume(queue='fuzz_results', on_message_callback=self.callback)
            print(" [*] Python Brain Consumer waiting for results on 'fuzz_results'...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ connection failed (will retry): {e}")

def run_consumer_in_background():
    """
    Spawns the blocking pika consumer inside a daemon thread 
    so it doesn't block the FastAPI application loop.
    """
    consumer = ResultConsumer()
    thread = threading.Thread(target=consumer.start_consuming, daemon=True)
    thread.start()
