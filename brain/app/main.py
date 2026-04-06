from fastapi import FastAPI
import os

app = FastAPI(title="XForge Brain API", description="Autonomous Offensive Security Intelligence Layer")

@app.on_event("startup")
async def startup_event():
    print("XForge Brain initializing...")
    # Initialize DB connections, Redis, and RabbitMQ (Chunk 3/4)

@app.get("/")
def read_root():
    return {"status": "XForge Brain is operational", "components": "waiting for tasks"}

@app.post("/tasks")
def create_task(target: str):
    # This will trigger the Recon Agent and drop messages into RabbitMQ for the Executor
    return {"message": f"Task created for {target}. Recon started."}
