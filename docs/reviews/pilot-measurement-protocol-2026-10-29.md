# 试点度量协议（2026-10-29）

> 目的：让“误杀 / 漏放 / 周期 / 绕过”从口号变成可计算数据，再用数据校准门数量和阈值。
> 本文件只定义**怎么测**，不改门数/阈值/阻断权。

## 0. 当前基线（必须先承认）

- 已完成 4 个变更：UX-01 D1、UX-02 D0、UX-03 D1、UX-04 D1。
- 有效独立样本约 1 个完整链（UX-01）；D2/D3 为 0。
- 误杀/漏放正式率：**unknown**；周期只有墙钟；绕过已发现 3 类。
- 因此：**现在不能调阈值/门数**；当前是案例研究，不是校准实验。

## 1. 单位与口径

| 指标 | 单位 | 定义 |
|---|---|---|
| 误杀 false positive | **finding** | 门判 blocking/major，但独立复核证明问题不成立/不必要/严重度虚高 |
| 漏放 false negative | **finding/事件** | 发布后发现、且按当时门规格本应抓住的缺陷或验收缺失 |
| 周期 cycle | **变更** | 主动审阅分钟数（不是墙钟）；墙钟另记 |
| 绕过 bypass | **门事件** | 未过必需门、批准后代码变更、无 A9 例外等 |

- nit/格式类被标成 conditional：单独记 `severity_overkill`，**不算误杀**。
- 发布后问题若属于“产品新决定”而非门漏，记 `product_change`，不算漏放。

## 2. 记录规则

- **事件时记录**：review 开始、结束、决定、merge、CI、post-release 检查都当场写。
- 时间不确定就留空，禁止回填假时间；`time_quality=recorded/backfilled/unknown`。
- 批准必须绑定 `approval_binding_commit`；合并 commit 另记。
- 每个 finding 有 ID、严重度、门、reviewer、最终处置（fixed/accepted/rejected/invalid）。
- 独立 review 报告必须单独落盘；聊天结论不算。
- 字段见 `pilot-log-v2-schema-2026-10-29.md`。

## 3. 角色与判定

| 角色 | 职责 |
|---|---|
| Builder | 实现、修复、提供证据；**不能给自己签 RG3** |
| Independent reviewer | 写 review 报告、给 finding；不参与实现 |
| Process owner | 维护协议、抽查记录、主持误杀/漏放判定 |
| Release owner | RG3 签字；对残余风险做 A9 |

误杀/漏放判定会：独立 reviewer + builder + process owner；有分歧记两方观点，不强行统一。

## 4. 四指标的采集

### 4.1 误杀

- 每个 blocking/major finding 在修复/发布后由非作者复核：
  - `valid`：问题成立且严重度合理；
  - `severity_overkill`：问题成立但严重度虚高；
  - `invalid`：问题不成立/不必要。
- 误杀率 = `invalid / (blocking+major findings)`；`severity_overkill` 单独统计。

### 4.2 漏放

- 发布后 2–4 周回查：用户反馈、issue、监控、产品验收缺口。
- 每个漏放记录：现象、发现时间、应被哪道门抓住、为什么没抓住（规格/执行/角色/工具）。
- 漏放率 = `漏放事件 / 变更数`；同时按严重度分。

### 4.3 周期

- 记录 `review_started_at`、`review_decided_at`（主动审阅），计算分钟。
- 墙钟另记（含等待/过夜/等签字），不用于成本结论。
- 报告：中位数、p90；样本 <5 时只列原始值。

### 4.4 绕过

分类计数：

1. 跳过必需门（如 D1 的 RG0/RG1）；
2. 批准后新增 code/deps/schema commit 未复审；
3. 批准 binding commit ≠ merge commit；
4. 缺失必需门（OG0/TG）且无 A9；
5. 先合并后补门；
6. 口头批准/无书面记录。

每类记 `bypass=1 + reason + a9_id`；**禁止用 bypass=0 掩盖例外**。

## 5. 样本与节奏

| 目的 | 样本 |
|---|---|
| 看方向 | 5–10 个变更 + 上线后 2–4 周 |
| 粗估误杀/漏放率（±20%） | 20–30 个/**档位**，D0/D1/D2/D3 分开 |
| 门数量/阈值校准 | 10–20 个代表性变更，先 shadow 2–3 再 enforce |
| 周期中位数/p90 | 5–10 个看中位数；20+ 看 p90 |

**第一个正式检查点：10 个变更**，至少 D0≥3、D1≥5、D2≥1、独立报告≥7 份。
- 每 5 个变更做一次小复盘；
- 每个变更发布后 2–4 周回查；
- 未到检查点前，不改门数/阈值/阻断权。

## 6. 门调整规则（以后才用）

- 先 shadow：新门/阈值只记录不阻断 2–3 个变更；
- 再 enforce：有数据支持才转阻断；
- 每次调整记 A9：依据、预期收益、可能误杀、复审日期；
- 一次只改一个变量（门数、阈值、阻断权分开）。

## 7. 当前残余与下一步

- 5 步 legacy 组件未挂载：另开清理，不混入校准。
- 埋点无消费端：第 5 个变更做 D2 first-party analytics，补 D2 样本。
- 主指标未执行：UX-01 可用性测试记为延期，后续补；不追溯改结论。
- UX-04 是“修复复盘发现的问题”，不计为新的门有效性证据。

## 8. 产物

- 门记录：`pilot-log-v2-2026-10-29.csv`
- 单变更 review：`review-*-2026-*.md`
- 发布包：`release-rg3-*-2026-*.md`
- 复盘：`pilot-retro-2026-10-29.md`
- 本协议：`pilot-measurement-protocol-2026-10-29.md`
