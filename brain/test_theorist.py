import pytest
import json
from app.theorist import TheoristAgent

@pytest.mark.asyncio
async def test_generate_hypotheses(mocker):
    # Mock OpenAI response
    mock_response = mocker.MagicMock()
    mock_choice = mocker.MagicMock()
    mock_choice.message.content = json.dumps({
        "workflows": [
            {
                "attack_type": "bola",
                "payloads": [
                    {"method": "GET", "path": "/api/test", "headers": {}, "body": ""}
                ]
            }
        ]
    })
    mock_response.choices = [mock_choice]
    
    agent = TheoristAgent()
    mock_create = mocker.AsyncMock(return_value=mock_response)
    mocker.patch.object(agent.llm_client.chat.completions, 'create', new=mock_create)
    
    spec = {"paths": {"/api/test": {}}}
    
    workflows = await agent.generate_hypotheses(spec, "bola", 1)
    
    assert len(workflows) == 1
    assert workflows[0]["attack_type"] == "bola"
    assert workflows[0]["payloads"][0]["path"] == "/api/test"
