package recon

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
)

// SubfinderResult represents a single JSON output line from Subfinder
type SubfinderResult struct {
	Host   string `json:"host"`
	Source string `json:"source"`
}

// SubfinderWrapper handles the execution of ProjectDiscovery's subfinder tool.
type SubfinderWrapper struct {
	BinaryPath string
}

// NewSubfinderWrapper creates a new wrapper, defaulting to "subfinder" in the PATH.
func NewSubfinderWrapper(path string) *SubfinderWrapper {
	if path == "" {
		path = "subfinder"
	}
	return &SubfinderWrapper{BinaryPath: path}
}

// Run executes subfinder against a target domain and parses the JSON output.
func (s *SubfinderWrapper) Run(domain string) ([]SubfinderResult, error) {
	// Execute subfinder with JSON output and silent mode
	cmd := exec.Command(s.BinaryPath, "-d", domain, "-json", "-silent")
	
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("subfinder execution failed: %v (stderr: %s)", err, stderr.String())
	}

	return s.parseOutput(out.Bytes())
}

func (s *SubfinderWrapper) parseOutput(data []byte) ([]SubfinderResult, error) {
	var results []SubfinderResult
	lines := bytes.Split(data, []byte("\n"))

	for _, line := range lines {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		
		var res SubfinderResult
		if err := json.Unmarshal(line, &res); err != nil {
			// Skip lines that aren't valid JSON (sometimes tools print banner/errors to stdout)
			continue
		}
		results = append(results, res)
	}

	return results, nil
}
