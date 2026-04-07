import pytest
import json
from app.modules.injection import InjectionModule

def test_identify_injection_targets():
    mock_spec = {
        "paths": {
            "/api/search": {
                "get": {
                    "parameters": [{"name": "q", "in": "query"}]
                }
            },
            "/api/user/{id}": {
                "get": {
                    "parameters": [{"name": "id", "in": "path"}]
                },
                "post": {} # Should be caught because it's a POST
            },
            "/api/health": {
                "get": {} # Should be ignored (no params, not POST)
            }
        }
    }
    
    module = InjectionModule("test_token")
    targets = module.identify_targets(mock_spec)
    
    assert len(targets) == 3
    paths = [t["path"] for t in targets]
    assert "/api/search" in paths
    assert "/api/user/{id}" in paths
    assert "/api/health" not in paths

def test_generate_injection_workflows():
    module = InjectionModule("test_token")
    targets = [
        {
            "path": "/api/search",
            "method": "GET",
            "parameters": [{"name": "q", "in": "query"}]
        },
        {
            "path": "/api/create",
            "method": "POST",
            "parameters": []
        }
    ]
    
    tasks = module.generate_workflows("https://test.com", targets)
    
    assert len(tasks) == 2
    
    # Check GET query injection
    task1 = tasks[0]
    assert task1["attack_type"] == "injection"
    assert len(task1["payloads"]) > 0
    # The first payload is an SQLi payload injected into the 'q' parameter
    assert "?q=" in task1["payloads"][0]["path"]
    
    # Check POST body injection
    task2 = tasks[1]
    assert task2["attack_type"] == "injection"
    assert len(task2["payloads"]) > 0
    
    p = task2["payloads"][0]
    assert p["method"] == "POST"
    assert p["headers"]["Content-Type"] == "application/json"
    
    # Ensure body is valid JSON and contains the payload
    body_dict = json.loads(p["body"])
    assert "data" in body_dict
    assert isinstance(body_dict["data"], str)
