import pytest
from app.result_consumer import ResultConsumer
import json

def test_consumer_callback_parses_recon_json(mocker):
    # Mock DB
    mock_db = mocker.patch("app.result_consumer.SessionLocal")
    mock_session = mocker.MagicMock()
    mock_db.return_value = mock_session
    
    mock_task = mocker.MagicMock()
    mock_task.id = 1
    mock_task.target_id = 99
    mock_session.query().filter().first.return_value = mock_task
    
    mock_parser_class = mocker.patch("app.result_consumer.ReconParser")
    mock_parser_instance = mock_parser_class.return_value
    
    consumer = ResultConsumer()
    
    mock_ch = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = "tag-recon-123"
    
    # Subfinder Payload (Wrapped correctly in the Go FuzzResult 'Error' field as a JSON string array)
    subfinder_array = '[{"host": "api.test.com", "source": "certspotter"}]'
    # We must properly escape the inner quotes for the outer JSON load to work
    escaped_array = subfinder_array.replace('"', '\\"')

    body = f'{{"task_id": "task-1-uuid", "attack_type": "subfinder_scan", "target_url": "http://test.com", "results": [{{"Error": "{escaped_array}"}}]}}'.encode('utf-8')
    
    consumer.callback(mock_ch, mock_method, None, body)
    
    # Verify the message was acknowledged
    mock_ch.basic_ack.assert_called_once_with(delivery_tag="tag-recon-123")
    
    # Verify ReconParser was initialized and called
    mock_parser_class.assert_called_once_with(mock_session, 99)
    mock_parser_instance.ingest_subfinder.assert_called_once_with([{"host": "api.test.com", "source": "certspotter"}])
    
    # Assert DB commit was called
    mock_session.commit.assert_called_once()
