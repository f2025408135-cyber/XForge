package fuzzer

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/xforge/executor/pkg/evasion"
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
	evasion     *evasion.EvasionEngine
}

// NewEngine creates an execution engine capable of concurrent multi-step attacks.
func NewEngine(client *httpclient.FuzzClient, concurrency int) *Engine {
	if concurrency <= 0 {
		concurrency = 10 // Safe default
	}
	return &Engine{
		client:      client,
		concurrency: concurrency,
		evasion:     evasion.NewEvasionEngine(),
	}
}

// ExecuteTask runs a messaging.TaskPayload (which contains a series of payloads/states).
func (e *Engine) ExecuteTask(task messaging.TaskPayload) ([]FuzzResult, error) {
	if len(task.Payloads) == 0 {
		return nil, fmt.Errorf("task %s has no payloads to execute", task.TaskID)
	}

	log.Printf("Executing task %s (%s) with %d payloads against %s", task.TaskID, task.AttackType, len(task.Payloads), task.TargetURL)

	if task.AttackType == "race_condition" {
		return e.executeRaceCondition(task)
	}

	return e.executeSequentialPool(task)
}

func (e *Engine) executeSequentialPool(task messaging.TaskPayload) ([]FuzzResult, error) {
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

				// Basic active WAF evasion logic
				// If we get blocked on the very first try, apply generic evasion techniques
				// and fire the exact same request again transparently before sending failure back to Python.
				if resp.StatusCode == 403 || resp.StatusCode == 406 {
					resp.Body.Close()
					
					// Deep copy request since bodies are consumed
					var retryBody io.Reader
					if job.Payload.Body != "" {
						retryBody = bytes.NewBuffer([]byte(job.Payload.Body))
					}
					retryReq, _ := http.NewRequest(job.Payload.Method, targetURI, retryBody)
					for k, v := range job.Payload.Headers {
						retryReq.Header.Set(k, v)
					}
					
					// Apply Evasion Engine Mutators
					e.evasion.ApplyAll(retryReq)
					
					retryStart := time.Now()
					retryResp, retryErr := e.client.Do(retryReq)
					
					if retryErr == nil {
						resp = retryResp
						duration = time.Since(retryStart)
						job.Payload.Path = retryReq.URL.String() // Note the mutation path for reporting
					}
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

func (e *Engine) executeRaceCondition(task messaging.TaskPayload) ([]FuzzResult, error) {
	// Race conditions require strict parallel execution. We prep all requests, hold them at a sync point, and fire simultaneously.
	resultsChan := make(chan FuzzResult, len(task.Payloads))
	
	var wg sync.WaitGroup
	var startWg sync.WaitGroup
	
	startWg.Add(1) // Block all workers until we trigger this WaitGroup

	for _, p := range task.Payloads {
		wg.Add(1)
		go func(payload struct {
			Method  string            `json:"method"`
			Path    string            `json:"path"`
			Headers map[string]string `json:"headers"`
			Body    string            `json:"body"`
		}) {
			defer wg.Done()
			
			targetURI := task.TargetURL + payload.Path
			var reqBody io.Reader
			if payload.Body != "" {
				reqBody = bytes.NewBuffer([]byte(payload.Body))
			}

			req, err := http.NewRequest(payload.Method, targetURI, reqBody)
			if err != nil {
				resultsChan <- FuzzResult{Error: err.Error(), Method: payload.Method, Path: payload.Path}
				return
			}
			for k, v := range payload.Headers {
				req.Header.Set(k, v)
			}

			// Block here until startWg.Done() is called from the main thread
			startWg.Wait()

			start := time.Now()
			resp, err := e.client.Do(req)
			duration := time.Since(start)

			if err != nil {
				resultsChan <- FuzzResult{Error: err.Error(), Method: payload.Method, Path: payload.Path, Duration: duration}
				return
			}

			bodyBytes, _ := io.ReadAll(resp.Body)
			resp.Body.Close()

			resultsChan <- FuzzResult{
				Method:     payload.Method,
				Path:       payload.Path,
				StatusCode: resp.StatusCode,
				BodyLen:    len(bodyBytes),
				Duration:   duration,
			}
		}(p)
	}

	// Wait a tiny fraction of a second for all goroutines to queue up and hit startWg.Wait()
	time.Sleep(50 * time.Millisecond)

	// Unleash all requests simultaneously
	startWg.Done()
	
	wg.Wait()
	close(resultsChan)

	var results []FuzzResult
	for res := range resultsChan {
		results = append(results, res)
	}

	return results, nil
}
