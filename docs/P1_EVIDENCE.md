# P1 证据索引

> 实现日：2026-11-14（Asia/Shanghai）。  
> 人工验收：2026-11-15 → **complete（mock / 原型，不是生产）**，见 [P1_ACCEPTANCE.md](P1_ACCEPTANCE.md)。  
> Draft 为 **mock**（`draft_pr.json`），非生产 GitHub 写入。

| ID | 证据 |
|---|---|
| P1-A | `pytest` `test_p1_a_*`；demo `artifacts/p1-demo/**/report.json` 含稳定 `plan_sha256` |
| P1-B | `test_p1_b_*`；shadow `external_writes=[]`、`draft_pr=null` |
| P1-C | `test_p1_c_*`；缺 `plan_sha256` 拒绝；匹配后可 guarded |
| P1-D | `test_p1_d_*`；demo negative：错误指纹无 Draft |
| P1-E | `test_p1_e_*`；`allow_external_write=false` 无写；`true` 产出 mock Draft |
| P1-F | `test_p1_f_*`；`reject_body_actor`；仅 `X-Actor-Id` 信任头 |
| P1-G | `test_p1_g_*`；`trajectory.format-b.json` 含 Format B 必填字段 |
| P1-H | `test_p1_h_*`；仓内无 `react_loop` / `.go` / `go.mod` |

命令：

```powershell
python -m pytest -q
python demos/run_p1_demo.py
```
