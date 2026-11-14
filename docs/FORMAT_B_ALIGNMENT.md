# Format B 契约对齐（P1）

本仓不迁 `react-agent` 的 Harness / `react_loop`。P1 只产出**字段级兼容**的 Format B 轨迹 JSON：

| 字段 | 要求 |
|---|---|
| `session_id` | 非空 |
| `query` | 非空 |
| `steps` | 至少 1 步 |
| `final_answer` | 字符串（可描述失败） |

可选：`schema_version`、`format`、`task_episode_id`、`acceptance_criteria`、`model`、`timestamp`。

参考 schema（只读）：`react-agent/schemas/harness_trajectory.schema.json` 与 `trace-debugger` 的 `agent_trajectory.schema.json`。  
产物路径约定：`artifacts/**/trajectory.format-b.json`。
