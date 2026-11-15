# P1 人工验收记录

> 验收日：2026-11-15（Asia/Shanghai）  
> 对照：[P1-SLICE.md](P1-SLICE.md) P1-A … P1-H  
> **裁决：complete（mock / 原型，不是生产）**

## 复跑证据

| 命令 | 结果 |
|---|---|
| `python -m pytest -q` | **8 passed** |
| `python demos/run_p1_demo.py` | shadow ok；guarded 产出 `draft_pr.json`（`mock: true`）；负例指纹不一致 → `ok: false`、无 Draft |

本轮 demo 指纹：`plan_sha256=f6fa51721af9548ec3e78ff49ad12d4c55f7a2b5ba5b9ede7f8545c2e7d485f0`  
产物目录：`artifacts/p1-demo/`（本地，不入库）。

## 逐项裁决

| ID | 裁决 | 依据 |
|---|---|---|
| P1-A | **pass** | 夹具 `fixtures/issue.json` → shadow `report.json` 含可复现 `plan_sha256` 与 `plan.issue_id` 等绑定字段；两次 shadow 指纹一致 |
| P1-B | **pass** | `mode=shadow`；`external_writes=[]`；`draft_pr=null`；无 GitHub 写接口调用 |
| P1-C | **pass** | 缺 `plan_sha256` 的 approval → guarded 失败；指纹一致且字段齐全 → 可进入 guarded |
| P1-D | **pass** | 篡改指纹负例：`negative_ok=false`，`negative_draft=null`，错误信息要求重新 shadow/审批 |
| P1-E | **pass** | `allow_external_write=false` 无外部写；`true` 时写出 mock Draft（`draft: true`, `mock: true`） |
| P1-F | **pass** | Actor 仅来自信任头 `X-Actor-Id`（`source=trust_header`）；body 冒充 `actor_id`/`user_id` 被拒（`test_p1_f_*`） |
| P1-G | **pass** | `trajectory.format-b.json` 含 `session_id`/`query`/`steps`/`final_answer`；见 [FORMAT_B_ALIGNMENT.md](FORMAT_B_ALIGNMENT.md) |
| P1-H | **pass** | 目录审查与 `test_p1_h_*`：无 `react_loop` 迁入、无 `.go`/`go.mod` |

## 边界声明（过关仍成立）

- Draft 为 **mock 文件证据**，不是生产 GitHub App / 真实 PR 生命周期。
- 本切片是 **可演示原型**，不是可发布生产系统；**不得**写成简历「已完成可发布产品」。
- 未开 Go / P2；未迁 `react-agent` 循环或仓库结构。
