# 受控变更交付（change-delivery）

独立产品：把 Issue / 任务单经影子执行与人工审批后开出 Draft PR。

**P0 立项已过关。P1 最小演示已实现（mock Draft），待人工过关；过关前不要写入简历。**

主路径：读 Issue → 影子执行 → 人工审批（钉死 `plan_sha256`）→ 才开 Draft PR。审批通过后不得改计划再开 PR。

## 快速演示

```powershell
python -m pytest -q
python demos/run_p1_demo.py
```

或：

```powershell
$env:PYTHONPATH = "src"
python -m change_delivery.cli shadow --issue fixtures/issue.json --artifact-dir artifacts/manual --actor-id demo
# 把 report 里的 plan_sha256 写入 approval.json 后：
python -m change_delivery.cli guarded --issue fixtures/issue.json --artifact-dir artifacts/manual --approval approval.json --actor-id demo
```

## 文档

- [范围说明](docs/SCOPE.md)
- [P1 验收口径](docs/P1-SLICE.md)
- [P1 证据索引](docs/P1_EVIDENCE.md)
- [Format B 对齐](docs/FORMAT_B_ALIGNMENT.md)

## 相邻仓库（不合并）

| 仓库 | 角色 |
|---|---|
| `react-agent` | 工作助手；只对齐权限/轨迹/审批契约，不迁循环或仓库结构 |
| `trace-debugger` | 轨迹失败雷达与 CI 钩子，不做最终裁决 |
| `llm-eval-engine` | 发版前自检（pass / review / hold） |

## 明确不做（P1）

- 不从 `react-agent` 迁代码，不写 Go 服务
- Draft 默认为本地 mock 证据，不是生产 GitHub App 接入
