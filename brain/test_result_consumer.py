import pytest
from app.result_consumer import ResultConsumer
from app.models import Task, Finding

def test_consumer_callback_parses_json(mocker):
    # We mock the DB so we don't need a real SQLite connection for unit test
    mock_db = mocker.patch("app.result_consumer.SessionLocal")
    mock_session = mocker.MagicMock()
    mock_db.return_value = mock_session
    
    mock_task = mocker.MagicMock()
    mock_task.id = 1
    mock_task.attack_type = "bola"  # <----- Missing! The feedback_loop checks `task.attack_type == "bola"` !
    mock_session.query().filter().first.return_value = mock_task
    
    # We mock it here:
    mock_evaluator_cls = mocker.patch("app.feedback_loop.EvaluatorAgent")
    mock_eval_instance = mock_evaluator_cls.return_value
    mock_eval_instance.evaluate_bola.return_value = {
        "vuln_score": 0.9,
        "findings": ["BOLA Verified"]
    }
    
    # Mock memory and theorist so ChromaDB and LLM aren't initialized
    mocker.patch("app.feedback_loop.PayloadMemory")
    mocker.patch("app.feedback_loop.TheoristAgent")

    mock_poc = mocker.patch("app.result_consumer.PoCGenerator")
    mock_poc.create_poc_bundle.return_value = {"curl": "curl mock"}
    
    consumer = ResultConsumer()
    
    # Mock pika channel and method
    mock_ch = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = "tag123"
    
    # Valid Payload
    body = b'{"task_id": "task-1-uuid", "attack_type": "bola", "target_url": "http://test.com", "results": [{"Method": "GET", "Path": "/api/users/2"}]}'
    
    consumer.callback(mock_ch, mock_method, None, body)
    
    # Verify the message was acknowledged
    mock_ch.basic_ack.assert_called_once_with(delivery_tag="tag123")
    
    # Verify evaluate_bola was called
    mock_eval_instance.evaluate_bola.assert_called_once()
    
    # Verify Finding was added to DB because score > 0
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
