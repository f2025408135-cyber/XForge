package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/xforge/executor/pkg/messaging"
)

func main() {
	fmt.Println("XForge Executor Engine Starting...")

	amqpURL := os.Getenv("RABBITMQ_URL")
	if amqpURL == "" {
		amqpURL = "amqp://xforge:xforge_password@localhost:5672/"
	}

	consumer, err := messaging.NewConsumer(amqpURL, "fuzz_tasks")
	if err != nil {
		log.Printf("Warning: Failed to connect to RabbitMQ (is it running?): %v", err)
	} else {
		defer consumer.Close()

		fmt.Println("Connected to RabbitMQ. Waiting for fuzzing tasks...")
		
		err = consumer.StartListening(func(task messaging.TaskPayload) {
			log.Printf("Received Task [%s]: Initiating %s attack against %s", task.TaskID, task.AttackType, task.TargetURL)
			// Trigger Go-based fuzzer workers here (Chunk 5)
		})
		
		if err != nil {
			log.Fatalf("Error starting consumer: %v", err)
		}
	}

	// Keep the microservice running
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	
	<-sigs
	fmt.Println("\nShutting down XForge Executor gracefully.")
}
