package recon

import (
	"testing"
)

func TestNucleiParseOutput(t *testing.T) {
	wrapper := NewNucleiWrapper("")

	mockOutput := []byte(`{"template-id":"tech-detect","info":{"name":"Wappalyzer Technology Detection","author":["hakluke"],"tags":["tech"],"severity":"info"},"type":"http","host":"https://example.com","matched-at":"https://example.com","extracted-results":["PHP"],"ip":"93.184.216.34","timestamp":"2026-04-06T23:00:00Z"}
{"template-id":"cve-2021-44228","info":{"name":"Apache Log4j2 Remote Code Execution","author":["pdteam"],"tags":["cve","cve2021","rce","oast","log4j"],"severity":"critical"},"type":"http","host":"https://example.com","matched-at":"https://example.com/?q=test","ip":"93.184.216.34","timestamp":"2026-04-06T23:01:00Z"}
`)

	results, err := wrapper.parseOutput(mockOutput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("Expected 2 results, got %d", len(results))
	}

	// Test the info severity field parsing
	if results[0].Info.Severity != "info" {
		t.Errorf("Expected info severity, got %s", results[0].Info.Severity)
	}
	
	if results[1].Info.Severity != "critical" {
		t.Errorf("Expected critical severity, got %s", results[1].Info.Severity)
	}

	// Test array parsing
	if len(results[0].ExtractedResults) == 0 || results[0].ExtractedResults[0] != "PHP" {
		t.Errorf("Expected extracted result PHP, got %v", results[0].ExtractedResults)
	}

	// Test template ID
	if results[1].TemplateID != "cve-2021-44228" {
		t.Errorf("Expected CVE template ID, got %s", results[1].TemplateID)
	}
}
