import pytest
from app.evaluator import EvaluatorAgent
import json

def test_evaluate_bola_high_confidence():
    agent = EvaluatorAgent()
    mock_results = [
        {"method": "GET", "path": "/api/admin/data", "status_code": 200, "role": "admin", "body_len": 500},
        {"method": "GET", "path": "/api/admin/data", "status_code": 200, "role": "standard", "body_len": 498}
    ]
    
    evaluation = agent.evaluate_bola(mock_results)
    
    assert evaluation["vuln_score"] == 0.9
    assert "High confidence BOLA" in evaluation["findings"][0]

def test_evaluate_bola_blocked():
    agent = EvaluatorAgent()
    mock_results = [
        {"method": "GET", "path": "/api/admin/data", "status_code": 200, "role": "admin", "body_len": 500},
        {"method": "GET", "path": "/api/admin/data", "status_code": 403, "role": "standard", "body_len": 50}
    ]
    
    evaluation = agent.evaluate_bola(mock_results)
    
    assert evaluation["vuln_score"] == 0.0
    assert "Authorization boundary held firm" in evaluation["findings"][0]

@pytest.mark.asyncio
async def test_evaluate_complex_logic_flaw(mocker):
    # Mock LLM fallback evaluator
    mock_response = mocker.MagicMock()
    mock_choice = mocker.MagicMock()
    mock_choice.message.content = json.dumps({
        "is_vulnerable": True,
        "confidence": 0.85,
        "explanation": "Negative amount bypasses balance check"
    })
    mock_response.choices = [mock_choice]
    
    agent = EvaluatorAgent()
    mock_create = mocker.AsyncMock(return_value=mock_response)
    mocker.patch.object(agent.llm_client.chat.completions, 'create', new=mock_create)
    
    result = await agent.evaluate_complex_logic_flaw("Transfer -50", [{"status_code": 200, "body": "transfer successful"}])
    
    assert result["is_vulnerable"] is True
    assert result["confidence"] == 0.85
    assert "Negative amount" in result["explanation"]
