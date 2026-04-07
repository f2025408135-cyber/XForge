package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
	"net/url"

	"github.com/xforge/executor/pkg/fuzzer"
	"github.com/xforge/executor/pkg/httpclient"
	"github.com/xforge/executor/pkg/messaging"
	"github.com/xforge/executor/pkg/recon"
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
		
		publisher, err := messaging.NewPublisher(amqpURL, "fuzz_results")
		if err != nil {
			log.Printf("Warning: Failed to connect to publisher: %v", err)
		} else {
			defer publisher.Close()
		}

		// Initialize the high-concurrency Fuzz Client
		fuzzClient := httpclient.NewFuzzClient(httpclient.ClientOptions{
			Timeout:       10 * time.Second,
			MaxConns:      1000,
			SkipTLSVerify: true,
		})
		
		// Initialize the Execution Engine (default 50 concurrent workers)
		fuzzerEngine := fuzzer.NewEngine(fuzzClient, 50)

		err = consumer.StartListening(func(task messaging.TaskPayload) {
			log.Printf("Received Task [%s]: Initiating %s attack against %s", task.TaskID, task.AttackType, task.TargetURL)
			
			var results []messaging.FuzzResult
			
			switch task.AttackType {
			case "subfinder_scan":
				results = handleSubfinder(task)
			case "naabu_scan":
				results = handleNaabu(task)
			case "nuclei_scan":
				results = handleNuclei(task)
			default:
				// Execute dynamic multi-step fuzzing tasks (BOLA, Logic Abuse, Race Conditions)
				fuzzOut, err := fuzzerEngine.ExecuteTask(task)
				if err != nil {
					log.Printf("Task %s failed: %v", task.TaskID, err)
					return
				}
				
				for _, r := range fuzzOut {
					results = append(results, messaging.FuzzResult{
						Method:     r.Method,
						Path:       r.Path,
						StatusCode: r.StatusCode,
						BodyLen:    r.BodyLen,
						Duration:   r.Duration.String(),
						Error:      r.Error,
					})
				}
			}

			// Publish results back to Python Brain
			pubErr := publisher.PublishResult(messaging.ResultPayload{
				TaskID:     task.TaskID,
				AttackType: task.AttackType,
				TargetURL:  task.TargetURL,
				Results:    results,
			})
			
			if pubErr != nil {
				log.Printf("Failed to publish result for Task %s: %v", task.TaskID, pubErr)
			} else {
				log.Printf("Successfully published results for Task %s", task.TaskID)
			}
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

// Helpers to wrap OSS tool outputs into a standard format the Brain can ingest
func extractDomain(targetURL string) string {
	parsed, err := url.Parse(targetURL)
	if err == nil && parsed.Host != "" {
		return parsed.Host
	}
	return targetURL
}

func handleSubfinder(task messaging.TaskPayload) []messaging.FuzzResult {
	wrapper := recon.NewSubfinderWrapper("") // assumes binary in PATH
	domain := extractDomain(task.TargetURL)
	
	out, err := wrapper.Run(domain)
	if err != nil {
		log.Printf("Subfinder failed: %v", err)
		return nil
	}
	
	jsonBytes, _ := json.Marshal(out)
	return []messaging.FuzzResult{{BodyLen: len(jsonBytes), Error: string(jsonBytes)}}
}

func handleNaabu(task messaging.TaskPayload) []messaging.FuzzResult {
	wrapper := recon.NewNaabuWrapper("")
	domain := extractDomain(task.TargetURL)
	
	out, err := wrapper.Run(domain)
	if err != nil {
		log.Printf("Naabu failed: %v", err)
		return nil
	}
	
	jsonBytes, _ := json.Marshal(out)
	return []messaging.FuzzResult{{BodyLen: len(jsonBytes), Error: string(jsonBytes)}}
}

func handleNuclei(task messaging.TaskPayload) []messaging.FuzzResult {
	wrapper := recon.NewNucleiWrapper("")
	
	out, err := wrapper.Run(task.TargetURL)
	if err != nil {
		log.Printf("Nuclei failed: %v", err)
		return nil
	}
	
	jsonBytes, _ := json.Marshal(out)
	return []messaging.FuzzResult{{BodyLen: len(jsonBytes), Error: string(jsonBytes)}}
}
