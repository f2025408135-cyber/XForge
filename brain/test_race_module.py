import pytest
from app.modules.race import RaceConditionModule

def test_identify_race_targets():
    mock_spec = {
        "paths": {
            "/api/transfer": {
                "post": {"summary": "Transfer funds"}
            },
            "/api/user/profile": {
                "put": {"summary": "Update profile"}
            },
            "/api/redeem-coupon": {
                "post": {}
            }
        }
    }
    
    module = RaceConditionModule("test_token")
    targets = module.identify_targets(mock_spec)
    
    assert len(targets) == 2
    
    paths = [t["path"] for t in targets]
    assert "/api/transfer" in paths
    assert "/api/redeem-coupon" in paths
    assert "/api/user/profile" not in paths # PUT update profile is typically not high risk for state racing

def test_generate_race_workflows():
    module = RaceConditionModule("test_token")
    targets = [{"path": "/api/transfer", "method": "POST"}]
    
    tasks = module.generate_workflows("https://test.com", targets, concurrency_count=50)
    
    assert len(tasks) == 1
    task = tasks[0]
    
    assert task["attack_type"] == "race_condition"
    assert len(task["payloads"]) == 50
    assert task["payloads"][0]["path"] == "/api/transfer"
    assert task["payloads"][0]["headers"]["Authorization"] == "Bearer test_token"
