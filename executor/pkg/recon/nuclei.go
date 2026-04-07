package recon

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
)

// NucleiResult represents a single JSON output line from Nuclei
type NucleiResult struct {
	TemplateID string `json:"template-id"`
	Info       struct {
		Name     string   `json:"name"`
		Author   []string `json:"author"`
		Tags     []string `json:"tags"`
		Severity string   `json:"severity"`
	} `json:"info"`
	Type        string `json:"type"`
	Host        string `json:"host"`
	MatchedAt   string `json:"matched-at"`
	ExtractedResults []string `json:"extracted-results,omitempty"`
	IP          string `json:"ip,omitempty"`
	Timestamp   string `json:"timestamp"`
}

// NucleiWrapper handles the execution of ProjectDiscovery's nuclei tool.
type NucleiWrapper struct {
	BinaryPath string
}

// NewNucleiWrapper creates a new wrapper, defaulting to "nuclei" in the PATH.
func NewNucleiWrapper(path string) *NucleiWrapper {
	if path == "" {
		path = "nuclei"
	}
	return &NucleiWrapper{BinaryPath: path}
}

// Run executes nuclei against a target and parses the JSON output.
func (n *NucleiWrapper) Run(target string) ([]NucleiResult, error) {
	// Execute nuclei with JSON output and silent mode.
	// We might want to pass specific templates/tags in a real run, but this is the baseline.
	cmd := exec.Command(n.BinaryPath, "-u", target, "-json", "-silent")
	
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("nuclei execution failed: %v (stderr: %s)", err, stderr.String())
	}

	return n.parseOutput(out.Bytes())
}

func (n *NucleiWrapper) parseOutput(data []byte) ([]NucleiResult, error) {
	var results []NucleiResult
	lines := bytes.Split(data, []byte("\n"))

	for _, line := range lines {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		
		var res NucleiResult
		if err := json.Unmarshal(line, &res); err != nil {
			continue
		}
		results = append(results, res)
	}

	return results, nil
}
