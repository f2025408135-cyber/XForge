package fuzzer

import (
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"github.com/xforge/executor/pkg/httpclient"
	"github.com/xforge/executor/pkg/messaging"
)

func TestEngineExecuteTask(t *testing.T) {
	// Create mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") == "Bearer admin" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("admin access granted"))
		} else {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("access denied"))
		}
	}))
	defer server.Close()

	// Initialize FuzzClient and Engine
	client := httpclient.NewFuzzClient(httpclient.ClientOptions{
		Timeout:       2 * time.Second,
		SkipTLSVerify: true,
	})
	engine := NewEngine(client, 2) // 2 concurrent workers

	// Mock BOLA attack payload
	task := messaging.TaskPayload{
		TaskID:     "task-bola-test",
		TargetURL:  server.URL,
		AttackType: "bola",
		Payloads: []struct {
			Method  string            `json:"method"`
			Path    string            `json:"path"`
			Headers map[string]string `json:"headers"`
			Body    string            `json:"body"`
		}{
			{
				Method:  "GET",
				Path:    "/api/admin/users",
				Headers: map[string]string{"Authorization": "Bearer admin"},
				Body:    "",
			},
			{
				Method:  "GET",
				Path:    "/api/admin/users",
				Headers: map[string]string{"Authorization": "Bearer user"},
				Body:    "",
			},
		},
	}

	// Execute Task
	results, err := engine.ExecuteTask(task)
	if err != nil {
		t.Fatalf("Failed to execute task: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("Expected 2 results, got %d", len(results))
	}

	// Verify outcomes (Order might be random due to goroutines, so check both)
	foundAdmin := false
	foundUser := false

	for _, res := range results {
		if res.StatusCode == http.StatusOK {
			foundAdmin = true
			if res.BodyLen != len("admin access granted") {
				t.Errorf("Admin body length mismatch: expected %d, got %d", len("admin access granted"), res.BodyLen)
			}
		} else if res.StatusCode == http.StatusForbidden {
			foundUser = true
			if res.BodyLen != len("access denied") {
				t.Errorf("User body length mismatch: expected %d, got %d", len("access denied"), res.BodyLen)
			}
		} else {
			t.Errorf("Unexpected status code %d", res.StatusCode)
		}
	}

	if !foundAdmin || !foundUser {
		t.Errorf("Did not find both expected results: admin=%v, user=%v", foundAdmin, foundUser)
	}
}

func TestEngineExecuteRaceCondition(t *testing.T) {
	// We count how many requests arrive almost instantly
	var requestCount int
	var mu sync.Mutex

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		requestCount++
		mu.Unlock()
		
		// Simulate network processing time
		time.Sleep(10 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	client := httpclient.NewFuzzClient(httpclient.ClientOptions{
		Timeout:       2 * time.Second,
		SkipTLSVerify: true,
	})
	engine := NewEngine(client, 10) // Concurrency setting here shouldn't cap the race condition which spins its own massive goroutine pool

	// Construct 50 payloads
	payloads := make([]struct {
		Method  string            `json:"method"`
		Path    string            `json:"path"`
		Headers map[string]string `json:"headers"`
		Body    string            `json:"body"`
	}, 50)

	for i := 0; i < 50; i++ {
		payloads[i].Method = "POST"
		payloads[i].Path = "/api/race"
	}

	task := messaging.TaskPayload{
		TaskID:     "task-race-test",
		TargetURL:  server.URL,
		AttackType: "race_condition",
		Payloads:   payloads,
	}

	start := time.Now()
	results, err := engine.ExecuteTask(task)
	duration := time.Since(start)

	if err != nil {
		t.Fatalf("Failed to execute race condition: %v", err)
	}

	if len(results) != 50 {
		t.Fatalf("Expected 50 results, got %d", len(results))
	}

	// Because they execute concurrently rather than sequentially in a pool, 
	// 50 requests sleeping 10ms should take much closer to 10ms than 500ms.
	// Give generous overhead buffer for local execution (e.g. 200ms instead of 100ms)
	if duration > 250*time.Millisecond {
		t.Errorf("Race condition execution took too long (%v), not properly parallelized", duration)
	}

	mu.Lock()
	defer mu.Unlock()
	if requestCount != 50 {
		t.Errorf("Server only saw %d requests, expected 50", requestCount)
	}
}
