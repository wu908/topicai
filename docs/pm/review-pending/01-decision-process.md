# 决策简报 + 流程契约（pilot14，D1）

## 决策简报

- **问题**：周复盘「欠对账」只渲染前 3 条 pending（`ReviewPage.tsx:172`），第 4+ 条用户看不到、无法回填。
- **证据**：E1——`git grep pending.slice origin/main`；C1 的 A9-02 只覆盖已对照行，不含 pending 截断。
- **方案**：移除 `slice(0,3)`，沿用现有行/表单渲染全部 pending；更新 E2E 旧文案；补 4+ 条测试。
- **成功指标**：5 条 pending 全渲染；无新增控件；tsc/eslint/build/vitest 绿。
- **kill criteria**：若渲染全部导致不可接受的页面性能/可读性问题 → 回到「显示全部/收起」方案并重新 RG0；若部署演练失败 → 停止发布，只合并。
- **被接受风险**：长列表可读性（60 行上限内）；部署/回滚首次实测（用户已授权演练）。
- **设计门**：不新增界面元素；沿用原型周复盘右栏列表。
- **决策**：做（T0/D1）；决策人：用户（2026-10-31 授权 N1/N2）；日期：2026-10-31。

## 流程契约

```
项目：topicAI / mvp
变更：pilot14-review-pending（PILOT-14）
档位：T0 / D1（前端 1 页面 + 测试 + E2E 文案）
证据：E1（ReviewPage.tsx:172；C1 A9-02）
门：RG0 轻量（must-pass 1/2/3/4/6/8/10 + B-16 清单）→ RG1 not-triggered（5 类面逐条）→ 实现 → A5 → RG2（B-16 清单）→ merge
发布：release_trigger=deploy；RG3 + OG0 + A7；先部署→回滚演练，再部署（用户 2026-10-31 授权）
步骤：A0/A1+A3/A4 → RG0 → 实现 → A5 → RG2 → PR/CI → 合并 → RG3/OG0/A7 → 演练 → 部署 → 记录
决策人：用户（项目所有者）
批准记录：用户 2026-10-31 选 N1+N2；授权 N1 部署含回滚演练（_sync/p3/user-authorization-2026-10-31.md）
不变约束：不启用 analytics；不对真实库 --apply；不改 30 门/阈值/权威源
```
