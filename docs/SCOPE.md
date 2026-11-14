# 受控变更交付（change-delivery）范围说明

> 立项文档。本仓当前只有范围与边界，**没有可演示实现，不能当已完成项目写进简历**。
> 截止：2026-11-14（Asia/Shanghai）。机器：`79420da8-a929-4299-9d77-03fc2b3e7ab5`。

## 1. 产品是谁用、解决什么

| 项 | 说明 |
|---|---|
| 产品名 | 受控变更交付（change-delivery / 交付助手） |
| 使用者 | 需要把 Issue / 任务单变成受控代码变更的研发或平台同学（审批人、提交人角色分离） |
| 核心问题 | 在隔离环境里试改、试跑，经人工审批后再开 Draft PR；外部写入必须显式授权 |
| 不是什么 | 不是企业内部工作助手的第三场景；不是评测 SaaS；不是通用 Agent 框架 |

与工作助手（`react-agent` / work-assistant）的关系：**并列独立产品**，共用能力契约，不共用业务场景，不合并仓库，不并进工作助手交付线。

## 2. 主路径（唯一主线）

```text
Issue / 任务单
  → 读取与计划（计划指纹）
  → 隔离工作区影子执行（默认 shadow，不写源仓、不调 GitHub 写接口）
  → 测试 / 失败回归信号
  → 人工审批（绑定 plan_sha256）
  → 候选提交 → 可选 Draft PR（需显式 allow_external_write）
```

过关定义（立项阶段）：文档把「谁用、主路径、复用边界、非目标、Go 预留」写清即可。  
下一阶段（另开刀）才做**最小可演示切片**；本仓不在立项刀铺开后端。

## 3. 复用，不重造

从工作助手复用（稳定接口或共享包，**不复制实现、本阶段不迁代码**）：

| 能力 | 复用方式 | 禁止 |
|---|---|---|
| 权限 / Actor | 对齐服务端信任身份与 permission 闸门语义（如 `X-Actor-Id` → 服务端构造 Actor） | 从请求 body 授权 |
| 轨迹 | Format B 轨迹契约；产物可被质量仓消费 | 另造轨迹格式或把评测两仓并进来 |
| 审批 | 审批绑定计划指纹 / 版本 / hash；关单或通知成功 ≠ 批准变更 | 用「跑过测试」代替人工审批 |
| Agent 循环 | 继续使用现有 `react_loop` / ToolGuard 能力边界 | **用 Go 重写 `react_loop`** |

历史实现与沙箱证据仍在 `react-agent` 文档附录与 `agent-delivery-sandbox`；本仓立项后**不从 `react-agent` 拆业务线迁码**，演示切片另议。

## 4. Go 只预留服务侧模块

Go（若后续启用）只承担：

- webhook 接入与来源鉴权
- 任务队列与幂等键
- Episode / Artifact / PR 状态持久化
- GitHub API 与 PR 状态同步

**明确不做：** 用 Go 重写 Agent 循环、权限内核或轨迹运行时。  
立项阶段：**只写预留，不落地 Go 服务代码。**

## 5. 与另两仓的关系（独立、可编排）

```text
change-delivery 产出轨迹
  → trace-debugger：规则失败打标、scan/compare、CI 钩子（不做最终裁决）
  → llm-eval-engine：发版前自检 → pass / review / hold
```

三仓（加工作助手共四仓）保持独立 Git 仓库；可被 CI 编排，**不要合并，也不要把评测两仓改造成简历第二项**。

## 6. 非目标（立项即冻结）

- 不从 `react-agent` 迁代码、不拆工作助手业务线
- 不把规范咨询 / 报销办理并进本仓
- 不合并 `llm-eval-engine` / `trace-debugger`
- 不一次铺开后端、常驻调度、多租户或生产 SLA
- 不把 `react-agent` 内既有 GitHub 交付附录宣称为本仓已交付能力
- 简历：本仓在最小可演示切片过关前，**不得**写成已完成项目

## 7. 阶段闸门

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 立项 | 独立仓库 + 本范围说明 | **本刀目标** |
| P1 最小可演示切片 | 单主路径可本地跑通的影子→审批→Draft（范围另开刀冻结） | 未开始 |
| P2+ | Go 服务侧模块按需启用 | 未开始；依赖边界冻结 |

P0 过关后需人工确认，再开 P1；不要在本刀顺手实现 P1。

## 8. 参考（只读，不迁）

- 工作助手计划残页：`react-agent/docs/change-delivery-plan.md`
- 技术附录：`react-agent/docs/features/github-delivery-workflow.md`
- 沙箱仓：`weihuaguo270-ops/agent-delivery-sandbox`（`external_real_sandbox`，≠ 生产）
