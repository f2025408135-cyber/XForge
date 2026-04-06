package messaging

import (
	"encoding/json"
	"fmt"
	"log"

	amqp "github.com/rabbitmq/amqp091-go"
)

// TaskPayload matches the contracts/task_schema.json definition
type TaskPayload struct {
	TaskID     string `json:"task_id"`
	TargetURL  string `json:"target_url"`
	AttackType string `json:"attack_type"`
	Payloads   []struct {
		Method  string            `json:"method"`
		Path    string            `json:"path"`
		Headers map[string]string `json:"headers"`
		Body    string            `json:"body"`
	} `json:"payloads"`
}

// Consumer listens for FuzzTasks from the RabbitMQ queue
type Consumer struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	queue   amqp.Queue
}

// NewConsumer connects to RabbitMQ and declares the task queue
func NewConsumer(amqpURI, queueName string) (*Consumer, error) {
	conn, err := amqp.Dial(amqpURI)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to RabbitMQ: %w", err)
	}

	ch, err := conn.Channel()
	if err != nil {
		return nil, fmt.Errorf("failed to open a channel: %w", err)
	}

	q, err := ch.QueueDeclare(
		queueName,
		true,  // durable
		false, // delete when unused
		false, // exclusive
		false, // no-wait
		nil,   // arguments
	)
	if err != nil {
		return nil, fmt.Errorf("failed to declare a queue: %w", err)
	}

	// QoS to balance the load
	err = ch.Qos(1, 0, false)
	if err != nil {
		return nil, fmt.Errorf("failed to set QoS: %w", err)
	}

	return &Consumer{
		conn:    conn,
		channel: ch,
		queue:   q,
	}, nil
}

// StartListening begins consuming messages indefinitely
func (c *Consumer) StartListening(handler func(task TaskPayload)) error {
	msgs, err := c.channel.Consume(
		c.queue.Name,
		"",    // consumer tag
		false, // auto-ack (set to false to ensure tasks aren't lost if executor crashes)
		false, // exclusive
		false, // no-local
		false, // no-wait
		nil,   // args
	)
	if err != nil {
		return fmt.Errorf("failed to register a consumer: %w", err)
	}

	go func() {
		for d := range msgs {
			var task TaskPayload
			err := json.Unmarshal(d.Body, &task)
			if err != nil {
				log.Printf("Error decoding JSON task: %v", err)
				d.Nack(false, false) // discard unparseable message
				continue
			}

			// Pass the parsed task to the worker handler
			handler(task)

			// Acknowledge the message was processed successfully
			d.Ack(false)
		}
	}()

	return nil
}

// Close cleans up connections
func (c *Consumer) Close() {
	if c.channel != nil {
		c.channel.Close()
	}
	if c.conn != nil {
		c.conn.Close()
	}
}
