import pika
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://xforge:xforge_password@localhost:5672/")

def get_rabbitmq_channel():
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue='fuzz_tasks', durable=True)
        return connection, channel
    except Exception as e:
        print(f"Warning: Could not connect to RabbitMQ: {e}")
        return None, None

def publish_task(task_data: dict):
    """
    Publishes a task payload strictly following the contracts/task_schema.json structure.
    """
    conn, channel = get_rabbitmq_channel()
    if not channel:
        print("RabbitMQ not available, skipping message publish.")
        return False

    try:
        message = json.dumps(task_data)
        channel.basic_publish(
            exchange='',
            routing_key='fuzz_tasks',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        print(f" [x] Sent Task to queue: {task_data['task_id']}")
        return True
    except Exception as e:
        print(f"Failed to publish task: {e}")
        return False
    finally:
        if conn:
            conn.close()
