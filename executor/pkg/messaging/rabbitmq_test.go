package messaging

import (
	"encoding/json"
	"testing"
)

func TestTaskPayloadJSONParsing(t *testing.T) {
	jsonPayload := `{
		"task_id": "task-123-abc",
		"target_url": "https://example.com",
		"attack_type": "bola",
		"payloads": [
			{
				"method": "POST",
				"path": "/api/users",
				"headers": {"Authorization": "Bearer token"},
				"body": "{\"role\":\"admin\"}"
			}
		]
	}`

	var task TaskPayload
	err := json.Unmarshal([]byte(jsonPayload), &task)
	if err != nil {
		t.Fatalf("Failed to parse JSON: %v", err)
	}

	if task.TaskID != "task-123-abc" {
		t.Errorf("Expected task_id 'task-123-abc', got '%s'", task.TaskID)
	}
	if task.AttackType != "bola" {
		t.Errorf("Expected attack_type 'bola', got '%s'", task.AttackType)
	}
	if len(task.Payloads) != 1 {
		t.Fatalf("Expected 1 payload, got %d", len(task.Payloads))
	}
	if task.Payloads[0].Method != "POST" {
		t.Errorf("Expected method POST, got %s", task.Payloads[0].Method)
	}
}
