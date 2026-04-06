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
