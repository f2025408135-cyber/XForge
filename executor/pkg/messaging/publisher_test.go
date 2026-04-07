package messaging

import (
	"encoding/json"
	"testing"
)

func TestPublisherJSONSerialization(t *testing.T) {
	// A pure unit test, no active rabbitmq connection required
	payload := ResultPayload{
		TaskID:     "task-1-abc",
		AttackType: "bola",
		TargetURL:  "https://example.com",
		Results:    nil, // Empty results for simplicity
	}

	data, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("Failed to marshal ResultPayload: %v", err)
	}

	jsonStr := string(data)
	if jsonStr != `{"task_id":"task-1-abc","attack_type":"bola","target_url":"https://example.com","results":null}` {
		t.Errorf("Unexpected serialization: %s", jsonStr)
	}
}
