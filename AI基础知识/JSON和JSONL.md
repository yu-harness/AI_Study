**JSON**（`task_state.json`）：
```json
{
  "run_id": "run_001",
  "status": "running",
  "tool_steps": 0
}
```
**JSONL**（`trace.jsonl`）：
```
{"event": "run_started", "created_at": "12:00:00"}
{"event": "tool_executed", "name": "read_file", "created_at": "12:00:03"}
{"event": "tool_executed", "name": "run_shell", "created_at": "12:00:07"}
```

**JSONL = JSON Lines，每行都是一个独立、完整的 JSON 对象。**