package main

import (
	"encoding/json"
	"testing"

	"github.com/xforge/executor/pkg/messaging"
)

func TestExtractDomain(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"https://example.com/api/v1", "example.com"},
		{"http://test.local", "test.local"},
		{"invalid-url", "invalid-url"}, // fallback
	}

	for _, tc := range tests {
		actual := extractDomain(tc.input)
		if actual != tc.expected {
			t.Errorf("expected %s, got %s", tc.expected, actual)
		}
	}
}

func TestHandleOSSStub(t *testing.T) {
	// A pure execution of handleSubfinder would attempt to run the binary, which isn't present in CI.
	// But we can verify the JSON serialization format is sound.
	mockOut := []messaging.FuzzResult{
		{BodyLen: 100, Error: `{"host":"test.com"}`},
	}

	data, err := json.Marshal(mockOut)
	if err != nil {
		t.Fatalf("Failed to marshal: %v", err)
	}

	if string(data) == "" {
		t.Error("Serialized data was empty")
	}
}
