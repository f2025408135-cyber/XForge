import os
import shutil
import pytest
from app.memory import PayloadMemory

# Setup persistent directory for testing
TEST_DB_PATH = "./test_chroma_data"

@pytest.fixture(scope="function")
def memory():
    # Setup
    os.environ["CHROMA_DB_PATH"] = TEST_DB_PATH
    mem = PayloadMemory()
    yield mem
    # Teardown
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH, ignore_errors=True)

def test_store_and_retrieve_success(memory):
    memory.store_success(
        task_id="task-123",
        attack_type="sqli",
        payload_json='{"body": "\' OR 1=1 --"}',
        description="Bypassed basic auth with boolean injection"
    )
    
    # Wait for embedding to index (usually instant locally, but just ensuring)
    results = memory.retrieve_similar_payloads("sqli", "basic auth bypass", n_results=1)
    
    assert len(results) == 1
    assert "OR 1=1" in results[0]
    assert "sqli" in results[0]

def test_retrieve_empty_memory(memory):
    results = memory.retrieve_similar_payloads("bola", "testing unpopulated", n_results=1)
    assert len(results) == 0
