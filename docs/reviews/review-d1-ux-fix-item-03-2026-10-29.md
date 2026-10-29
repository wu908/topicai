# D1 独立 review 报告（转录）· UX-03 项目屏阶段条

> 来源：`d1-reviewer`（fresh context、可见 teammate）只读 review 输出，由 Lead 转录为仓库工件。
> 原始 review：2026-10-28 17:00–17:02 首审 + 17:13/17:17 delta 复审；最终 `approve`。
> 审查对象：`4dee3ed` → `d7cd326` → `40d6e6b` → `569f9d5`（最终）；base `586270c`。
> **注意：本文件是 reviewer 输出的转录，不是 Lead 自审；原始对话仍是事实源。**

- 结论：**approve**（含 delta）；0 blocking / 0 major；首审有 7 个 nit/观察，delta 修复后仅剩已知 F2 产品决策与命名 nit。
- 变更范围：12 文件（前端内容/样式/测试 + docs/screenshots）；无后端/schema/依赖变更。

## 验证

| 项 | 结果 |
|---|---|
| 单条 bar | 项目屏只剩 1 个 `[aria-current="step"]`；标签：想清楚/找素材/写初稿/发前检查/观察 |
| now 文案 | 使用 `activeActionTitle`，优先 workspace action；cancelled/completed 回退 |
| 产物栏 | 不再渲染 StageBar；「下一步」KV 与 bar 同源 |
| 测试 | 3 suites 39 passed（ProjectStagePage 18 / ArtifactPane 16 / ProjectDetailPane 5）；model 20 |
| 类型/lint | `tsc -b` / `eslint .` 通过 |
| 视觉 | 1440/390 单条 bar、5 标签、now 文案正常；截图已刷新 |
| 全量 | 486 tests passed（RG3 复核） |

## 主要 findings / 修复

1. **now 文案与确认卡不一致**：bar 用 `nextActionLabel(project)`，未用 workspace action；修复为 `activeActionTitle`。
2. **cancelled/completed action 仍显示“现在做”**：allow-list 只接受 `proposed/accepted/deferred`；补测试。
3. **bar 与产物“下一步”两套文案**：统一到 `activeActionTitle`。
4. **单条 bar 重复**：移除 ArtifactPane 的 StageBar；ProjectChat 不再包第二层 `.stages`。
5. **测试未钉高亮步/全标签**：补 5 标签 + `写初稿` `aria-current` + exact now。
6. **legacy StageMeter 注释过期**：已修。
7. **视觉证据 stale**：KV 改动后重拍 1440/390。

## 已知未闭环（非阻塞）

- **F2**：`stageOf(record_publication)=3` → 项目屏高亮“写初稿”，而列表同状态是“去发布”。属于产品语义决策；本次未改。
- `data-testid="stage-meter"` 沿用旧名，未改为 `project-flow-bar`。
- 未跑 axe 全量；未做真实后端 HTTP 集成。

## 判定

**RG2（D1）通过**；无 blocking/major，剩余为已知产品决策/命名 nit。
