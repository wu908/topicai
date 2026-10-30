# A0/A1 · 清除被删组件的私有死 CSS（pilot 10，D0）

> 工件：A0/A1｜版本 v1 · 2026-10-30｜档位 **T0 / D0**
> 证据：pilot9 RG1 m3 / pilot6 RG1 m5——删除 `ViewpointPanel`/`SeriesPanel`/`WorkspaceAiDock` 后，其私有 CSS（`.viewpoint-*`/`.series-*`/`.genome-context*`/`.workspace-eyebrow`）已无使用者。

## 1. 问题与范围

- 问题：`ContentPage.css` 仍保留约 40 组只服务已删组件的样式规则，增加噪声并误导后来者。
- 范围（1 文件）：`frontend/src/pages/Content/ContentPage.css`——删除选择器全部命中上述前缀的死规则（含媒体查询内规则），保留其他样式与注释；不重排格式。
- 非目标：不改任何在用类、不改组件、不格式化整个文件；`workspace-header` 等同源死 CSS 记 backlog，后续单独清理（RG2-m1）。

## 2. 验收

| # | 标准 |
|---|---|
| A1 | 死前缀 **CSS 0 命中**（`frontend/src` 另有 4 处 API 路由字符串 `viewpoint-candidates`/`creator-series-candidates`，非样式，不计） |
| A2 | `vite build` / `tsc` / eslint 0；全量 vitest 绿（59/467） |
| A3 | 删除仅做整块删除（无其他改动/无重排），diff 全部为删除 |
| A4 | 界面无变化（无对应元素使用这些类） |

## 3. 风险与回滚

- 风险：误删与其他选择器共享的规则 → 已确认无混合选择器；删除后 build/测试验证。
- 回滚：`git revert 4c18470`。
