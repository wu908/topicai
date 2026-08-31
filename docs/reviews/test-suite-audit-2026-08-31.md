# 测试套件审计报告

**日期**：2026-08-31
**范围**：后端 389 tests（覆盖率 88%）+ 前端 222 tests（覆盖率门禁 lines 80 / funcs-br-stmt 55）+ E2E 3 个 spec
**方法**：覆盖率 term-missing 全量分析 + 反模式全库 grep（两端）+ 核心契约测试抽样深读（test_intent_driven_actions 1613 行等）+ 对本会话新增测试的自审
**总评**：**套件整体健康，未发现任何"断言造假"级问题**。契约测试文化扎实（HTTP 层走真实 envelope、幂等与属主隔离成对出现、断言密度高——核心契约文件 204 断言/1613 行）。风险集中在 5 个具体缺口（§4），全部可低成本补齐。

---

## 1. 断言真实性（有无假断言）

**结论：真实。**

| 检查项 | 结果 |
|---|---|
| 裸 `assert True` / 恒真断言 | 0 |
| `pytest.raises(Exception)` 宽泛捕获 | 0（本会话曾引入 4 处，已全部收敛为具体异常） |
| `.only`/`skip` 欠账 | 0 |
| 幂等重放断言 | 用 `meta.idempotency_replayed` + 状态码 201→200 的**行为证据**，非 mock 自证 |
| 唯一软点 | `test_experiment_metrics.py:324` 一处 `xfail(strict=False)`（已知 flaky ~15%，注明 ADR-003）——即复盘文档"1 xpassed"债。**建议**：要么定位根因转正，要么改 `strict=True` + skip 并挂 issue，避免长期模糊 |

**前端的一个结构性弱点（非造假，但要知道边界）**：10/10 页面测试文件全部 mock 掉 API 层——断言的是"给定 mock 响应时页面的行为"，**捕获不了前后端契约漂移**。现有三层缓解（TS 类型编译期校验、后端 HTTP 契约测试、/loop 已有真栈 E2E）使该风险可控；但新增端点在 E2E 覆盖前存在"两端类型各自演进"的窗口期。

## 2. 完整性（覆盖率与行为缺口）

### 2.1 后端（88%，门禁 80%）

值得补的弱模块（已排除"设计上走 mock"的项）：

| 模块 | 覆盖 | 缺口性质 |
|---|---|---|
| `app/core/rate_limiter.py` | 44% | 限流器的拒绝分支无测试——是安全相关行为，**建议补** |
| `app/api/v2/auth.py` | 50% | 登录/refresh 错误分支（401/429）未覆盖——**建议补** |
| `app/api/v2/creator_rules.py` | 62% | 路由层错误路径 |
| `app/services/intent_actions.py` | 77%（缺 119 行） | 两整块：175–241（动作生命周期）、1271–1301（自动化偏好）——编排核心，**建议补** |
| 可接受项 | `llm.py` 45%（真实调用路径设计上由 fake/降级路径覆盖）、`deps.py` 27%（注入装饰器） | 不必强补 |

### 2.2 行为级缺口（具体到断言）

1. `pickup` 的 `schedule_at` 落库路径（COALESCE 分支）无断言；
2. `sweep_expired` 的属主隔离未测（A 的过期清扫不得动 B）；
3. `consent=private 不进生产`仅服务级测试，API 层无复验；
4. E2E 仅 3 个 spec：loop 的 discard/过期/货架限流无浏览器级链路；"拾取→内容页→发布检查"跨页链路只有单页断言。

### 2.3 前端

门禁存在且记录了演进史（ADR-001：lines 80%，branches/functions/statements 55%）。branches 55% 偏松，条件渲染多的页面（拾取面板展开态）值得在下一阶段把 branches 抬到 65%。

## 3. 合理性

- **金字塔形态正确**：服务级为主 → HTTP 契约次之 → E2E 冒烟（3 spec/36+62+9 断言级 expect），与"本地 MVP + 高速回归"的定位匹配；
- **时间依赖已防雷**：测试用固定历史日期 + 可调 `days` 参数，无 Date.now 依赖（PR #34 date-bomb 教训已制度化）；但 `_published_project` 助手硬编码 `2026-07-21`，所有依赖 7 天窗口的断言依赖调用方记得传 `days`——**建议改动态日期**（见 §5 P1）；
- **隔离性好**：每测试独立 in-memory 库 + 自建 user；`insert_user` 用户名撞库问题本会话已修；
- **自曝一处耦合**：`test_weekly_review.py` 与 `test_async_loop_api.py` 从 `test_creator_series` 导入 `_published_project` 助手——跨测试模块 import 制造隐式耦合，**建议提取到 `tests/helpers/`**。

## 4. 断言合理性（强度抽评）

- **强断言的范例**（值得保持的模式）：周复盘对 `judgment.audience_change` 具体值断言；async loop 对事实溯源 `facts[0].source_inbox_id == item["id"]` 的逐条断言；预检 `precheck.passed is True`；
- **可接受偏松**：货架限流断言 `>=6` 而非 `==6`（预算语义使然）；`content_intent in (set)` 而非精确映射断言；
- **脆弱点**：前端 `getAllByText` 多元素兜底是为对抗"同一标题出现在产出卡与周复盘行"的合理选择，但建议对关键行加 `within()` 作用域限定，防误报漏报。

## 5. 建议清单

| 优先级 | 项 | 成本 |
|---|---|---|
| P0 | xfail 转正/转 skip+issue（消除长期 flaky 模糊） | 0.5h |
| P0 | `rate_limiter` 拒绝分支 + `auth.py` 错误路径补测 | 2h |
| P1 | `_published_project` 日期动态化 + 提取 `tests/helpers/` | 1h |
| P1 | 补 pickup.schedule_at、sweep 属主隔离、private-API 层三条断言 | 1.5h |
| P2 | intent_actions 两块缺口（175–241、1271–1301） | 3h |
| P2 | 前端 branches 55→65%；loop 的 discard/E2E 链路补全 | 3h |
