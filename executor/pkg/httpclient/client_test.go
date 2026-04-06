package httpclient

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestFuzzClient_NoProxy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	client := NewFuzzClient(ClientOptions{
		Timeout:       2 * time.Second,
		SkipTLSVerify: true,
	})

	req, err := http.NewRequest("GET", server.URL, nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Failed to execute request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}
}

func TestFuzzClient_ProxyRotation(t *testing.T) {
	client := NewFuzzClient(ClientOptions{
		Proxies: []string{"http://proxy1.local", "http://proxy2.local"},
	})

	// Test the round robin logic
	req, _ := http.NewRequest("GET", "http://example.com", nil)
	
	url1, _ := client.rotateProxy(req)
	if url1.String() != "http://proxy1.local" {
		t.Errorf("Expected proxy1.local, got %s", url1.String())
	}

	url2, _ := client.rotateProxy(req)
	if url2.String() != "http://proxy2.local" {
		t.Errorf("Expected proxy2.local, got %s", url2.String())
	}

	url3, _ := client.rotateProxy(req)
	if url3.String() != "http://proxy1.local" {
		t.Errorf("Expected proxy1.local on wrap around, got %s", url3.String())
	}
}
