# A0/A1 · AI 断网文案人话化（pilot 7，D0）

> 工件：A0/A1 合并简版（D0 轻量）｜版本 v1 · 2026-10-30｜档位 **T0 / D0**
> 证据：UX 审计 2026-10-21 P0-6「AI 断网时把 `Failed to fetch` 直接吐给用户」；本次复核：`CompanionDialog.tsx:156` 与 `FieldSuggestions.tsx:67` 仍用 `extractErrorMessage`，未走 `extractModelErrorMessage`。

## 1. 问题与范围

- 问题：AI 对话/字段建议在断网时可能显示 `Failed to fetch` / `NetworkError` 等英文技术词，零基础用户看不懂。
- 范围（2 文件 + 2 测试）：
  - `frontend/src/features/companion/CompanionDialog.tsx`：错误改用 `extractModelErrorMessage`；
  - `frontend/src/features/content/FieldSuggestions.tsx`：同上；
  - 两个测试各补一条 `Failed to fetch` → 中文友好文案的用例。
- 非目标：不改错误工具函数本身、不改其他组件、不改 UI/接口。

## 2. 验收（可判定）

1. AI 对话与字段建议在 `Failed to fetch` 时显示「模型暂时连不上，你的输入还在，可以稍后重试。」；
2. 不再显示英文 `Failed to fetch`；
3. 其他错误文案不变（如 `AI 服务不可用` 仍原样显示）；
4. `vitest` 目标套件 + 全量绿；`tsc`/`eslint`/`build` 绿。

## 3. 风险

低：只改错误映射与测试；可 revert；无接口/数据/UI 结构变化。
