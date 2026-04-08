package recon

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
)

// KatanaResult represents a single JSON output line from ProjectDiscovery's Katana crawler
type KatanaResult struct {
	Timestamp string `json:"timestamp"`
	Request   struct {
		Method   string `json:"method"`
		Endpoint string `json:"endpoint"`
		Body     string `json:"body"`
		Headers  map[string]string `json:"headers"`
	} `json:"request"`
	Response struct {
		StatusCode int `json:"status_code"`
	} `json:"response"`
}

// KatanaWrapper handles the execution of the modern web crawler Katana.
type KatanaWrapper struct {
	BinaryPath string
}

// NewKatanaWrapper creates a new wrapper, defaulting to "katana" in the PATH.
func NewKatanaWrapper(path string) *KatanaWrapper {
	if path == "" {
		path = "katana"
	}
	return &KatanaWrapper{BinaryPath: path}
}

// Run executes Katana against a target domain/URL and parses the JSON output.
func (k *KatanaWrapper) Run(target string) ([]KatanaResult, error) {
	// Execute katana with JSON output, silent mode, crawling headless, and capturing parameters
	cmd := exec.Command(k.BinaryPath, "-u", target, "-jsonl", "-silent", "-jc", "-headless")
	
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("katana execution failed: %v (stderr: %s)", err, stderr.String())
	}

	return k.parseOutput(out.Bytes())
}

func (k *KatanaWrapper) parseOutput(data []byte) ([]KatanaResult, error) {
	var results []KatanaResult
	lines := bytes.Split(data, []byte("\n"))

	for _, line := range lines {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		
		var res KatanaResult
		if err := json.Unmarshal(line, &res); err != nil {
			// Skip malformed JSON lines
			continue
		}
		results = append(results, res)
	}

	return results, nil
}
