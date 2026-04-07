import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from app.modules.logic_flow import LogicFlowModule

@pytest.mark.asyncio
async def test_generate_abuse_workflows(mocker):
    # Mock the TheoristAgent
    mock_theorist = MagicMock()
    mock_theorist.llm_client = MagicMock()
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "workflows": [
            {
                "attack_type": "logic_abuse",
                "payloads": [
                    {"method": "POST", "path": "/api/checkout", "headers": {}, "body": ""},
                    {"method": "POST", "path": "/api/cart", "headers": {}, "body": ""}
                ]
            }
        ]
    })
    mock_response.choices = [mock_choice]
    
    mock_create = AsyncMock(return_value=mock_response)
    mocker.patch.object(mock_theorist.llm_client.chat.completions, 'create', new=mock_create)
    
    module = LogicFlowModule(mock_theorist)
    
    spec = {"paths": {"/api/cart": {}, "/api/checkout": {}}}
    
    tasks = await module.generate_abuse_workflows("https://test.com", spec, "mock_token")
    
    assert len(tasks) == 1
    task = tasks[0]
    
    assert task["attack_type"] == "logic_abuse"
    assert "logic-run-" in task["task_id"]
    assert len(task["payloads"]) == 2
    
    # Assert token injection
    p1 = task["payloads"][0]
    assert p1["headers"]["Authorization"] == "Bearer mock_token"
    assert p1["path"] == "/api/checkout"
