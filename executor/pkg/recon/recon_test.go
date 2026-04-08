package recon

import (
	"testing"
)

func TestSubfinderParseOutput(t *testing.T) {
	wrapper := NewSubfinderWrapper("")

	mockOutput := []byte(`{"host":"api.example.com","source":"certspotter"}
{"host":"dev.example.com","source":"crtsh"}
`)

	results, err := wrapper.parseOutput(mockOutput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("Expected 2 results, got %d", len(results))
	}

	if results[0].Host != "api.example.com" {
		t.Errorf("Expected api.example.com, got %s", results[0].Host)
	}
}

func TestNaabuParseOutput(t *testing.T) {
	wrapper := NewNaabuWrapper("")

	mockOutput := []byte(`{"host":"example.com","ip":"93.184.216.34","port":80}
{"host":"example.com","ip":"93.184.216.34","port":443}
`)

	results, err := wrapper.parseOutput(mockOutput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("Expected 2 results, got %d", len(results))
	}

	if results[1].Port != 443 {
		t.Errorf("Expected port 443, got %d", results[1].Port)
	}
}

func TestKatanaParseOutput(t *testing.T) {
	wrapper := NewKatanaWrapper("")

	mockOutput := []byte(`{"timestamp":"2023-01-01T00:00:00Z","request":{"method":"GET","endpoint":"https://example.com/api/v1/users","body":"","headers":{"User-Agent":"Katana"}},"response":{"status_code":200}}
{"timestamp":"2023-01-01T00:00:01Z","request":{"method":"POST","endpoint":"https://example.com/login","body":"username=admin&password=123","headers":{"Content-Type":"application/x-www-form-urlencoded"}},"response":{"status_code":403}}
`)

	results, err := wrapper.parseOutput(mockOutput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("Expected 2 results, got %d", len(results))
	}

	if results[0].Request.Endpoint != "https://example.com/api/v1/users" {
		t.Errorf("Expected GET users endpoint, got %s", results[0].Request.Endpoint)
	}

	if results[1].Request.Method != "POST" || results[1].Response.StatusCode != 403 {
		t.Errorf("Expected POST with 403 status, got %s with %d", results[1].Request.Method, results[1].Response.StatusCode)
	}
}
