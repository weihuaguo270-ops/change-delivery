# P1 最小可演示切片 — 验收口径（已冻结）

> 冻结日：2026-11-14（Asia/Shanghai）。  
> 本页只定**做什么才算过关**；**本刀不写业务代码**。实现另开刀。  
> 上位边界见 [SCOPE.md](SCOPE.md)。

## 1. 切片目标

在本仓用**最小实现**本地跑通唯一主路径一次：

```text
读 Issue → 影子执行 → 人工审批（钉死 plan_sha256）→ 才开 Draft PR
```

证明：计划指纹可观测、审批与指纹绑定、指纹不一致时拒绝开 PR。  
不证明：生产可用性、多租户、常驻调度、Go 服务、质量仓深度集成。

## 2. 过关判定（全部满足才算 P1 complete）

| ID | 验收项 | 可观察证据 |
|---|---|---|
| P1-A | 能读入一条合成 / 夹具 Issue（或任务单 JSON），产出可复现的 `plan_sha256` | 影子报告含 `plan_sha256` 与输入绑定字段 |
| P1-B | 默认 `shadow`：不修改源仓库、不调用 GitHub 写接口 | 报告 `mode=shadow`；无 push / create PR 副作用 |
| P1-C | 人工审批文件 / 记录必须携带与影子报告一致的 `plan_sha256` | 指纹一致时允许进入 guarded；缺字段或为空则拒绝 |
| P1-D | 审批通过后若计划变更（`plan_sha256` 不一致），**不得**开 Draft PR | 负例：改计划或换指纹 → 明确失败，无 Draft |
| P1-E | 仅当指纹一致且显式 `allow_external_write`（或等价开关）时，才创建 Draft PR | 正例：一条 Draft（可用沙箱仓或 mock）；关闭开关则无外部写 |
| P1-F | 权限语义对齐：Actor / 审批身份不由请求 body 授权 | 文档 + 实现入口说明服务端构造 / 信任头；单测或夹具覆盖「body 冒充被拒」 |
| P1-G | 轨迹契约对齐 Format B（字段级兼容即可，不迁运行时） | 至少一份轨迹 / episode 产物可被声明为 Format B 兼容 |
| P1-H | 本仓无从 `react-agent` 迁入的循环实现或仓库结构拷贝；无 Go 服务代码 | 目录审查：无 `react_loop` 搬迁、无 Go webhook/队列实现 |

## 3. 建议演示命令形态（实现时再落脚本名）

```text
1) shadow  : 读夹具 Issue → 写出 report.json（含 plan_sha256）
2) approve : 生成 approval.json，plan_sha256 = report 中的值
3) guarded : 带 approval + allow_external_write → Draft PR 或等价外部写证据
4) negative: 篡改 plan_sha256 或改计划再跑 → 必须失败且无 Draft
```

具体 CLI / 包名在实现刀选定；口径不绑定必须复用 `react-agent` 的 `demos/run_github_delivery.py`。

## 4. 明确不在 P1

- 不迁 `react-agent` 代码、不搬 `react_loop` / 目录结构
- 不写 Go（webhook / 队列 / PR 持久化等留 P2+）
- 不接真实邮件 / IM、常驻调度、多租户、生产 SLA
- 不把 `llm-eval-engine` / `trace-debugger` 并进本仓（最多文档说明「轨迹可被其消费」）
- 不要求接生产 GitHub App；Draft 可用 sandbox 仓或受控 mock，但正例/负例都要有证据
- P1 complete **仍不是**简历「已完成可发布产品」；仅可写「受控变更交付最小演示」且须注明原型 / 沙箱

## 5. 与契约对齐的最低语义

| 契约 | P1 要对齐的语义 | 不对齐的做法 |
|---|---|---|
| 权限 | 服务端信任身份；副作用经闸门 | body 里带 user_id 当授权 |
| 审批 | 钉死 `plan_sha256`；通知/关单 ≠ 批准开 PR | 测试通过就自动开 PR |
| 轨迹 | Format B 兼容产物 | 另起不兼容私有格式且无映射说明 |

## 6. 阶段状态

| 项 | 状态 |
|---|---|
| P1 验收口径 | **已冻结**（本文） |
| P1 实现 | **进行中 / 待人工过关**；证据见 [P1_EVIDENCE.md](P1_EVIDENCE.md) |
| P2+ Go 服务侧 | 未开始；排在 P1 实现过关之后 |
