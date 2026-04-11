package evasion

import (
	"net/http"
	"net/url"
	"strings"
	"testing"
)

func TestSpoofHeaders(t *testing.T) {
	engine := NewEvasionEngine()
	req, _ := http.NewRequest("GET", "http://example.com", nil)

	engine.SpoofHeaders(req)

	if req.Header.Get("X-Forwarded-For") == "" {
		t.Error("Expected X-Forwarded-For header to be injected")
	}
	if req.Header.Get("X-Remote-IP") == "" {
		t.Error("Expected X-Remote-IP header to be injected")
	}
}

func TestNormalizePath(t *testing.T) {
	engine := NewEvasionEngine()

	// Because it relies on random, we will run it a few times and ensure it modifies the path correctly
	// without breaking the URL semantics.
	modified := false
	for i := 0; i < 10; i++ {
		req, _ := http.NewRequest("GET", "http://example.com/api/users", nil)
		engine.NormalizePath(req)
		
		if req.URL.Path != "/api/users" {
			modified = true
			if !strings.Contains(req.URL.Path, "//") && !strings.Contains(req.URL.Path, "/./") && !strings.HasSuffix(req.URL.Path, ".") {
				t.Errorf("Path mutated incorrectly: %s", req.URL.Path)
			}
			break
		}
	}

	if !modified {
		t.Error("NormalizePath failed to mutate the path after 10 attempts")
	}
}

func TestPolluteParameters(t *testing.T) {
	engine := NewEvasionEngine()

	// Test query injection
	req, _ := http.NewRequest("GET", "http://example.com/api/search?q=admin", nil)
	engine.PolluteParameters(req)

	query, _ := url.ParseQuery(req.URL.RawQuery)
	
	// Should have the original
	if !query.Has("q") {
		t.Error("Original parameter lost")
	}

	// Should have multiple values for 'q'
	if len(query["q"]) < 2 {
		t.Errorf("Expected parameter pollution on 'q', got values: %v", query["q"])
	}

	// Test adding junk to empty query
	reqEmpty, _ := http.NewRequest("GET", "http://example.com", nil)
	engine.PolluteParameters(reqEmpty)

	if reqEmpty.URL.RawQuery == "" {
		t.Error("Expected junk parameter injected on empty query string")
	}
}
