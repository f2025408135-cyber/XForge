package messaging

import (
	"encoding/json"
	"fmt"

	amqp "github.com/rabbitmq/amqp091-go"
)

// FuzzResult struct mirroring the fuzzer package to avoid import cycles.
type FuzzResult struct {
	Method     string `json:"Method"`
	Path       string `json:"Path"`
	StatusCode int    `json:"StatusCode"`
	BodyLen    int    `json:"BodyLen"`
	Duration   string `json:"Duration"`
	Error      string `json:"Error"`
}

// ResultPayload matches what the Python Brain's Evaluator expects.
type ResultPayload struct {
	TaskID     string       `json:"task_id"`
	AttackType string       `json:"attack_type"`
	TargetURL  string       `json:"target_url"`
	Results    []FuzzResult `json:"results"`
}

// Publisher handles sending FuzzResults back to the Python Brain via RabbitMQ.
type Publisher struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	queue   amqp.Queue
}

// NewPublisher connects to RabbitMQ and declares the results queue.
func NewPublisher(amqpURI, queueName string) (*Publisher, error) {
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

	return &Publisher{
		conn:    conn,
		channel: ch,
		queue:   q,
	}, nil
}

// PublishResult serializes and sends a ResultPayload to the queue.
func (p *Publisher) PublishResult(payload ResultPayload) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	err = p.channel.Publish(
		"",           // exchange
		p.queue.Name, // routing key
		false,        // mandatory
		false,        // immediate
		amqp.Publishing{
			ContentType:  "application/json",
			DeliveryMode: amqp.Persistent,
			Body:         data,
		},
	)

	if err != nil {
		return fmt.Errorf("failed to publish message: %w", err)
	}

	return nil
}

// Close cleans up connections.
func (p *Publisher) Close() {
	if p.channel != nil {
		p.channel.Close()
	}
	if p.conn != nil {
		p.conn.Close()
	}
}
