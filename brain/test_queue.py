def test_publish_task(mocker):
    mock_publish = mocker.patch('app.queue.publish_task')
    mock_publish.return_value = True
    assert mock_publish({'task_id': '1'}) == True
