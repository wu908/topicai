# Dependabot / 安全告警只读分级（2026-10-31）

> 范围：**只读分级，0 代码变更，不合并不改依赖**。用于 B-15 与 2027-01-31 季度决策前的批次准备。
> 数据：`gh pr list --state open`（18 个 PR，#38–#151）；`gh api repos/wu908/topicai/dependabot/alerts`（99 条，其中 open 68 条 = 45 条唯一 advisory；行级重复来自多 manifest/lock）。
> 基线：`origin/main = 1211cbf`；生产 `5751079`（2026-10-31 发布）。

## 1. 安全告警（open）

| 严重度（唯一 advisory） | 数量 |
|---|---|
| critical | **2** |
| high | **16** |
| medium | **22** |
| low | **5** |

| 包 | open 行数 | 说明 |
|---|---|---|
| pyjwt | 28 | 同一批 advisory 在 `pyproject.toml` / `requirements.txt` / lock 中重复计数 |
| undici | 11 | frontend 运行时（Node 内置 fetch 依赖） |
| starlette | 7 | backend 运行时（FastAPI 依赖） |
| react-router(-dom) | 6 | frontend 运行时 |
| @vitest/mocker / vitest | 6 | 开发依赖 |
| urllib3 | 3 | backend 运行时 |
| certifi | 1 | backend 运行时（**critical**） |
| 其他（pytest、brace-expansion、browserslist…） | 6 | 开发/构建依赖 |

**两条 critical**：

1. **certifi** `GHSA-6q48-6c7w-9gw2` — 内置 emSign 根 CA 的中间 CA 密钥被泄露（信任链风险）。修复 PR **#143**（certifi 2026.7.22 → 2026.10.19）。
2. **PyJWT** `GHSA-ffc3-869f-jxw9` — 非对称 PEM 检测绕过（空白/换行变异的公钥可跳过 HS/asymmetric 混淆防护）。修复 PR **#136**（pyjwt 2.8.0 → 2.15.0）。

> 另有多条 PyJWT high（如 `GHSA-pxh4-856f-4h89` 空 HMAC key 伪造、`GHSA-9v7f-9g4p-ffgj` JWKS 跟随重定向）——都与认证面相关，属 RG1 触发面（安全边界）。

## 2. 18 个 open PR 分级

| 批次 | PR | 内容 | 类型 | 风险/备注 |
|---|---|---|---|---|
| **0（安全优先）** | #143 | certifi 2026.7.22 → 2026.10.19 | runtime patch | critical；证书信任链；需 backend 测试 + 依赖锁同步 |
| 0 | #136 | pyjwt 2.8.0 → 2.15.0 | runtime minor | critical + 多条 high；**认证面，RG1 必做**；需 JWT 回归 |
| 0 | #137 | urllib3 2.7.0 → 2.8.0 | runtime minor | high（代理 TLS 配置 / 分块 DoS） |
| 0 | #151 | undici 7.29.0 → 7.30.1 | runtime patch | high（TLS 校验/缓存投毒/DoS）；frontend 依赖 |
| **1（patch/minor 批次）** | #149 | minor-and-patch 组（12 updates，frontend） | group | 与 #151/#52/#38 可能重叠，合并前重跑 CI |
| 1 | #40 | minor-and-patch 组（11 updates，backend） | group | 与 #137/#136 可能重叠 |
| 1 | #50 | react-router-dom 6.30.4 → 6.30.6 | runtime patch | 路由行为小改；E2E 冒烟 |
| 1 | #52 | baseline-browser-mapping 2.10.32 → 2.11.3 | dev minor | 仅构建数据 |
| 1 | #38 | browserslist 4.28.2 → 4.28.7 | dev patch | 构建工具；无运行时影响 |
| 1 | #53 | vitest 4.1.10 → 4.1.11 | dev patch | 测试工具 |
| **2（major，单独窗口）** | #49 / #46 | @mui/material、@mui/icons-material 5.18 → **9.4** | runtime **major** | 跨大版本，UI 全量回归 + 视觉回归 |
| 2 | #44 | openai 1.58 → **3.6** | runtime **major** | LLM 客户端 API 变更；影响 AI 功能 |
| 2 | #43 | mypy 1.13 → **2.3** | dev major | 类型检查规则变化，可能大量新错 |
| 2 | #41 | pytest 8.3 → **9.1** | dev major | 测试框架 |
| 2 | #42 | pytest-asyncio 0.24 → **1.4** | dev major | 异步测试语义变化 |
| 2 | #47 | jsdom 29 → **30** | dev major | 前端测试环境 |
| 2 | #48 | @testing-library/jest-dom 6.9 → **7.0** | dev major | 断言 API 变化 |

## 3. 建议（不执行）

1. **批次 0 单独 PR**：只动 certifi/pyjwt/urllib3/undici；PyJWT 属认证面 → RG1 触发，需 back-end 全量 + JWT 专项回归；不自动合并。
2. **批次 1**：按 group PR 优先（#149/#40），合并前 rebase 重跑 CI，避免重叠冲突。
3. **批次 2**：不在本季动；每项单独窗口 + 回归，纳入 2027-01-31 决策。
4. **度量**：合并批次 0 后复查 Dependabot 告警（预期 pyjwt 28 行大幅下降）；仍以 `gh api` 计数为准，不用“68”做目标值。
5. **不做**：不自动合并、不 `--apply`、不改生产、不在本 PR 动依赖。

## 4. 风险提示

- 安全告警数会随 advisory 更新变化；本文件是 **2026-10-31 快照**，不是长期结论。
- 同一 advisory 在多 manifest 重复计数，比较时应使用“唯一 advisory”口径（45），不要用 68 直接对外。
- Dependabot PR 长期滞留本身是风险（#38 创建于 2026-09-02，已近 2 个月）。
