# A0/A1 · ArtifactPane 断网文案人话化（pilot 8，D0）

> 工件：A0/A1 合并简版｜版本 v1 · 2026-10-30｜档位 **T0 / D0**
> 证据：pilot7 RG2 残留 m1「发前检查 `ArtifactPane.tsx` 仍用 `extractErrorMessage`，断网可能露英文」；UX 审计 P0-6 同类。

## 1. 问题与范围

- 问题：发前检查的「加载/运行」失败时，网络错误（`Failed to fetch`）会原样显示给用户。
- 范围（2 文件 + 测试）：
  - `frontend/src/features/content/ArtifactPane.tsx`：两处 `extractErrorMessage` → `extractModelErrorMessage`；
  - `ArtifactPane.test.tsx`：补 1 条断网 → 中文友好文案、且不出现 `Failed to fetch`。
- 非目标：不改其他组件、不改检查逻辑/接口。

## 2. 验收

1. 发前检查加载/运行时遇到 `Failed to fetch` 显示「模型暂时连不上，你的输入还在，可以稍后重试。」；
2. 不显示英文 `Failed to fetch`；
3. 非网络错误（如「发前检查服务不可用」「检查服务超时」）原样显示；
4. 全量测试/类型/lint/build 绿。

## 3. 风险

低：只改错误映射 + 测试；可 revert；无接口/数据/UI 结构变化。
