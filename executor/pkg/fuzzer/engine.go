package fuzzer

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/xforge/executor/pkg/httpclient"
	"github.com/xforge/executor/pkg/messaging"
)

// FuzzResult captures the outcome of a single mutated payload attempt.
type FuzzResult struct {
	Method     string
	Path       string
	StatusCode int
	BodyLen    int
	Duration   time.Duration
	Error      string
}

// Engine manages the execution of complex, multi-step vulnerabilities (BOLA, Race Conditions).
type Engine struct {
	client      *httpclient.FuzzClient
	concurrency int
}

// NewEngine creates an execution engine capable of concurrent multi-step attacks.
func NewEngine(client *httpclient.FuzzClient, concurrency int) *Engine {
	if concurrency <= 0 {
		concurrency = 10 // Safe default
	}
	return &Engine{
		client:      client,
		concurrency: concurrency,
	}
}

// ExecuteTask runs a messaging.TaskPayload (which contains a series of payloads/states).
func (e *Engine) ExecuteTask(task messaging.TaskPayload) ([]FuzzResult, error) {
	if len(task.Payloads) == 0 {
		return nil, fmt.Errorf("task %s has no payloads to execute", task.TaskID)
	}

	log.Printf("Executing task %s (%s) with %d payloads against %s", task.TaskID, task.AttackType, len(task.Payloads), task.TargetURL)

	results := make([]FuzzResult, 0, len(task.Payloads))
	
	// Channels for the worker pool
	jobs := make(chan struct {
		Index   int
		Payload struct {
			Method  string            `json:"method"`
			Path    string            `json:"path"`
			Headers map[string]string `json:"headers"`
			Body    string            `json:"body"`
		}
	}, len(task.Payloads))
	
	resultsChan := make(chan FuzzResult, len(task.Payloads))
	var wg sync.WaitGroup

	// Spin up workers
	for i := 0; i < e.concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for job := range jobs {
				targetURI := task.TargetURL + job.Payload.Path
				
				var reqBody io.Reader
				if job.Payload.Body != "" {
					reqBody = bytes.NewBuffer([]byte(job.Payload.Body))
				}

				req, err := http.NewRequest(job.Payload.Method, targetURI, reqBody)
				if err != nil {
					resultsChan <- FuzzResult{Error: err.Error(), Method: job.Payload.Method, Path: job.Payload.Path}
					continue
				}

				// Apply specific headers (e.g., Auth tokens for BOLA testing)
				for k, v := range job.Payload.Headers {
					req.Header.Set(k, v)
				}

				start := time.Now()
				resp, err := e.client.Do(req)
				duration := time.Since(start)

				if err != nil {
					resultsChan <- FuzzResult{Error: err.Error(), Method: job.Payload.Method, Path: job.Payload.Path, Duration: duration}
					continue
				}

				// Read response to calculate anomalies (size differences, unexpected status codes)
				bodyBytes, _ := io.ReadAll(resp.Body)
				resp.Body.Close()

				resultsChan <- FuzzResult{
					Method:     job.Payload.Method,
					Path:       job.Payload.Path,
					StatusCode: resp.StatusCode,
					BodyLen:    len(bodyBytes),
					Duration:   duration,
				}
			}
		}()
	}

	// Feed payloads into the job channel
	for i, p := range task.Payloads {
		jobs <- struct {
			Index   int
			Payload struct {
				Method  string            `json:"method"`
				Path    string            `json:"path"`
				Headers map[string]string `json:"headers"`
				Body    string            `json:"body"`
			}
		}{Index: i, Payload: p}
	}
	close(jobs)

	// Wait for workers to finish
	wg.Wait()
	close(resultsChan)

	// Collect results
	for res := range resultsChan {
		results = append(results, res)
	}

	return results, nil
}
