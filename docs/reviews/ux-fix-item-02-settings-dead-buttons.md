# UX-02 · 设置页死按钮禁用（D0）

- 日期：2026-10-28
- 状态：**RG2 通过（D0 快速独立 review）；待 RG3**
- 方向：审计 Q3 · **A：先禁用 + 标「即将上线」**（用户 2026-10-28 确认）
- 档位：**D0**（1 页面 + 测试；可逆；无接口/数据/权限变化）

## 1. 目标

设置页有 4 个按钮看起来可点，但没有任何动作：

- 配置模型…
- 管理权限…
- 导出…
- 申请删除…

目标：不再让用户误以为这些功能可用；明确告知「即将上线」。

## 2. 非目标

- 不实现模型配置、权限管理、导出、删号；
- 不新增后端/API/schema/迁移；
- 不改其他设置项；
- 不引入依赖。

## 3. 验收

- [x] 4 个按钮 `disabled`（含 `aria-disabled` 语义）；
- [x] 按钮文案或可见提示包含「即将上线」；
- [x] 点击不导航、不发请求（源码无 handler + 原生 disabled）；
- [x] 其他设置项不受影响；
- [x] 测试断言 4 个按钮禁用且无副作用；
- [x] `tsc` / ESLint / 目标测试通过。

## 4. 门禁（D0 路径）

- 跳过完整 RG0/RG1/三件套设计门（D0 小改）；
- 实现后：快速独立 review + RG3 发布证据；
- 试点记录：周期、误杀/漏放、绕过；与第 1 个 D1 对比。

## 5. 回滚

- 单 commit revert；无数据/接口影响。

## 6. 证据

- 变更文件：`frontend/src/pages/Settings/SettingsPage.tsx`、`frontend/src/pages/Settings/__tests__/SettingsPage.test.tsx`
- 4 个按钮：`disabled` + `title="即将上线"` + 文案「（即将上线）」
- 测试：`SettingsPage.test.tsx` **24 tests passed**
- `tsc -b`：通过
- `eslint .`：通过
- 源码核对：4 个按钮无新增 `onClick`；测试覆盖 disabled/title/可见「即将上线」
- 独立 review：**approve**，无 must-fix；3 条非阻塞 nit