package recon

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
)

// HttpxResult represents a single JSON output line from ProjectDiscovery's httpx
type HttpxResult struct {
	Timestamp string `json:"timestamp"`
	URL       string `json:"url"`
	Host      string `json:"host"`
	Port      string `json:"port"`
	Title     string `json:"title"`
	Tech      []string `json:"tech"`
	StatusCode int   `json:"status_code"`
	Words      int   `json:"words"`
	Lines      int   `json:"lines"`
}

// HttpxWrapper handles the execution of the httpx probing tool.
type HttpxWrapper struct {
	BinaryPath string
}

// NewHttpxWrapper creates a new wrapper, defaulting to "httpx" in the PATH.
func NewHttpxWrapper(path string) *HttpxWrapper {
	if path == "" {
		path = "httpx"
	}
	return &HttpxWrapper{BinaryPath: path}
}

// Run executes httpx against a list of domains/IPs to identify active web servers.
func (h *HttpxWrapper) Run(targets []string) ([]HttpxResult, error) {
	// For production, write targets to a temp file. We use bash piping here for simplicity in Go exec.
	targetList := ""
	for _, t := range targets {
		targetList += t + "\n"
	}

	cmd := exec.Command(h.BinaryPath, "-json", "-silent", "-tech-detect", "-title", "-status-code")
	
	// Pass targets via stdin
	cmd.Stdin = bytes.NewBufferString(targetList)
	
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("httpx execution failed: %v (stderr: %s)", err, stderr.String())
	}

	return h.parseOutput(out.Bytes())
}

func (h *HttpxWrapper) parseOutput(data []byte) ([]HttpxResult, error) {
	var results []HttpxResult
	lines := bytes.Split(data, []byte("\n"))

	for _, line := range lines {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		
		var res HttpxResult
		if err := json.Unmarshal(line, &res); err != nil {
			continue
		}
		results = append(results, res)
	}

	return results, nil
}
