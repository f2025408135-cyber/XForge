package fuzzer

import (
	"net/http"
	"net/http/httptest"
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
