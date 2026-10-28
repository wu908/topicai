# RG3 发布证据 · UX-02 设置页死按钮（D0）

- 日期：2026-10-28
- 分支：`pilot2-settings-dead-buttons`
- 基点：`9446204`（origin/main）
- 代码 HEAD：`24ae900`
- 状态：**Ready for RG3 human sign-off（待发布负责人签字）**
- 变更性质：前端禁用态 + 文案；**无后端、接口、schema、迁移、依赖变更**

## 1. 发布范围

设置页 4 个原本无动作的按钮：

- 配置模型…
- 管理权限…
- 导出…
- 申请删除…

改为 `disabled` + `title="即将上线"` + 文案「（即将上线）」；不实现功能。

## 2. 变更文件

- `frontend/src/pages/Settings/SettingsPage.tsx`
- `frontend/src/pages/Settings/__tests__/SettingsPage.test.tsx`
- `docs/reviews/ux-fix-item-02-settings-dead-buttons.md`

## 3. 验证证据

| 检查 | 结果 |
|---|---|
| 目标测试 | `SettingsPage.test.tsx` **24 tests passed** |
| 全量测试 | **64 files / 483 tests passed** |
| 覆盖率 | All files：lines 82.34 / functions 73.65 / branches 76.39 / statements 84.19（阈值 80/66/66/76） |
| 类型 | `tsc -b` 通过 |
| Lint | `eslint .` 通过 |
| 构建 | `vite build` 通过 |
| 代码 whitespace | `git diff --check 9446204..HEAD` 通过 |
| 独立 review | **approve**，无 must-fix；3 条非阻塞 nit |
| 后端/依赖 | 无变更 |

## 4. 风险与回滚

- 风险：低。只是禁用死按钮；用户不再误以为可用。
- 回滚：revert `24ae900`；无数据/接口/迁移影响。
- 非阻塞：未做浏览器截图；4 个按钮的 disabled/文案由 DOM 测试覆盖。

## 5. RG3 签字

| 项 | 结论 |
|---|---|
| 自动化验证 | ✅ |
| 独立 review | ✅ approve |
| 后端/数据风险 | ✅ 无 |
| 回滚可执行 | ✅ 单 commit |
| **发布负责人** | **待签字：可以合并 / 可以发布 / 暂不** |

## 6. 试点记录

- 档位：D0；与第 1 个 D1 变更对照。
- 是否需要完整 RG0/RG1：**否**，D0 豁免。
- 观察：门禁对小改是否过重、是否出现绕过。
