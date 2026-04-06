package recon

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
)

// NaabuResult represents a single JSON output line from Naabu
type NaabuResult struct {
	Host string `json:"host"`
	IP   string `json:"ip"`
	Port int    `json:"port"`
}

// NaabuWrapper handles the execution of ProjectDiscovery's naabu tool.
type NaabuWrapper struct {
	BinaryPath string
}

// NewNaabuWrapper creates a new wrapper, defaulting to "naabu" in the PATH.
func NewNaabuWrapper(path string) *NaabuWrapper {
	if path == "" {
		path = "naabu"
	}
	return &NaabuWrapper{BinaryPath: path}
}

// Run executes naabu against a target domain/IP and parses the JSON output.
func (n *NaabuWrapper) Run(target string) ([]NaabuResult, error) {
	// Execute naabu with JSON output and silent mode, fast port scan
	cmd := exec.Command(n.BinaryPath, "-host", target, "-json", "-silent", "-top-ports", "1000")
	
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("naabu execution failed: %v (stderr: %s)", err, stderr.String())
	}

	return n.parseOutput(out.Bytes())
}

func (n *NaabuWrapper) parseOutput(data []byte) ([]NaabuResult, error) {
	var results []NaabuResult
	lines := bytes.Split(data, []byte("\n"))

	for _, line := range lines {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		
		var res NaabuResult
		if err := json.Unmarshal(line, &res); err != nil {
			continue
		}
		results = append(results, res)
	}

	return results, nil
}
