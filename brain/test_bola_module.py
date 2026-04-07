import pytest
from app.modules.bola import BolaModule

def test_identify_targets():
    mock_spec = {
        "paths": {
            "/api/users/{id}": {
                "get": {},
                "put": {},
                "post": {}
            },
            "/api/health": {
                "get": {}
            },
            "/api/invoices/{invoice_id}/download": {
                "get": {}
            }
        }
    }
    
    module = BolaModule("admin_tok", "std_tok")
    targets = module.identify_targets(mock_spec)
    
    assert len(targets) == 3
    # Verify the paths matched
    paths = [t["path"] for t in targets]
    assert "/api/users/{id}" in paths
    assert "/api/invoices/{invoice_id}/download" in paths
    assert "/api/health" not in paths
    
    # Verify POST is correctly ignored on parameterized paths
    methods = [t["method"] for t in targets if t["path"] == "/api/users/{id}"]
    assert "GET" in methods
    assert "PUT" in methods
    assert "POST" not in methods

def test_generate_workflows():
    module = BolaModule("admin_tok", "std_tok")
    targets = [
        {"path": "/api/users/{id}", "method": "GET"}
    ]
    
    workflow = module.generate_workflows("https://example.com", targets)
    
    assert workflow["attack_type"] == "bola"
    assert workflow["target_url"] == "https://example.com"
    assert len(workflow["payloads"]) == 2
    
    # Check baseline (admin) payload
    p1 = workflow["payloads"][0]
    assert p1["method"] == "GET"
    assert p1["path"] == "/api/users/999"
    assert p1["headers"]["Authorization"] == "Bearer admin_tok"
    assert p1["headers"]["X-Role-Tag"] == "admin"
    
    # Check exploit (standard user) payload
    p2 = workflow["payloads"][1]
    assert p2["method"] == "GET"
    assert p2["path"] == "/api/users/999"
    assert p2["headers"]["Authorization"] == "Bearer std_tok"
    assert p2["headers"]["X-Role-Tag"] == "standard"
