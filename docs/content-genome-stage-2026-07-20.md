# TopicAI ContentGenome 阶段实施记录

## 阶段目标

把已经由用户确认、经过跨内容观察支持的创作者经验，组织成可检索、可解释、可追溯的决策图谱，并让它真正进入下一步行动的证据上下文。

本阶段的核心判断是：`ContentGenome` 不应该成为第二套可写规则数据库。现有 `CreatorRule`、不可变 `CreatorRuleVersion`、`Observation` 和冲突处理审计记录继续作为事实源；图谱只是它们的 owner-scoped read model。

## 已实现能力

### 后端

- 新增 `ContentGenomeService`，从激活规则、规则版本、规则冲突/例外和来源 Observation 派生图谱节点与边。
- 按项目检索时使用项目的内容意图、意图确认状态、目标受众和内容形式；实验条件可作为可选筛选项。
- 只把以下规则放入 `decision_context`：
  - 与当前内容意图一致；
  - 受众和形式范围匹配；
  - 来源 Observation 仍有效且达到既有最小样本要求；
  - 没有开放冲突或未分化的例外范围。
- 对被暂缓的规则保留节点和原因码，包括意图未确认、范围缺失、来源失效、开放冲突和已确认例外需要更多上下文。
- 新增查询接口：

```text
GET /api/v2/content-genome
GET /api/v2/projects/{project_id}/content-genome
```

- 图谱输出包含 `nodes`、`edges`、`decision_context`、`summary` 和稳定 `fingerprint`。
- 图谱指纹进入 `NextBestAction.expected_state_change`。规则或适用性发生变化时，旧行动会被标记为过期并按新图谱上下文重建。
- `AITrace` 记录图谱指纹、规则来源引用和实际使用边界；不把被冲突或失效的规则冒充为可用经验。

### 前端

- 内容项目工作台新增“本次 AI 实际参考 / 你的已验证经验”区域。
- 每条经验显示跨内容观察数量和来源项目数量。
- 当规则因范围、来源或冲突被暂缓时，明确显示暂缓数量。
- 没有适用经验时，明确说明 AI 只使用当前项目中已确认的信息。
- 新增 v2 API 客户端方法，支持通用图谱检索和项目图谱检索。

## 产品边界

- 不新增 `content_genome` 数据表，不复制规则、Observation 或用户事实。
- 不使用向量相似度替代适用范围判断。
- 不把规则样本数转换为“爆款概率”、流量预测或精确置信分。
- 不自动合并规则，不自动解决冲突，不自动把 AI 推断写入长期经验。
- `experiment` 在项目未明确填写时不作为硬过滤条件，因为现有规则中的实验字段首先描述被验证的内容实验；一旦项目明确实验，则严格排除不匹配规则。
- 未确认内容意图时，图谱可以展示可追溯节点，但不向 AI 行动上下文提供规则。

## 关键契约

```text
ContentGenome
  project_id
  query
  fingerprint
  nodes[]
  edges[]
  decision_context[]
  summary
```

`decision_context` 中的每条记录至少包含：规则版本引用、经验陈述、适用范围、Observation 引用、来源项目引用、样本数量和匹配原因。

## 验证结果

- 后端图谱/校准/意图行动定向测试：28 passed。
- 后端全量测试：728 passed，58 warnings；总覆盖率 85.56%。
- 前端图谱展示及冲突工作台定向测试：6 passed。
- 前端全量测试：50 files、331 passed、2 skipped。
- 前端 lint：通过。
- 前端 production build：通过。
- 开发后端健康检查：`http://127.0.0.1:8765/api/v2/health` 返回 200。
- OpenAPI 已暴露两个 ContentGenome 查询接口。
- 开发前端：`http://127.0.0.1:5177` 返回 200。

## 下一阶段

可复用 Evidence、观点显式确认和系列关系确认链路均已完成，详见 [ContentGenome Evidence 阶段实施记录](./content-genome-evidence-stage-2026-07-20.md)、[CreatorViewpoint 阶段实施记录](./creator-viewpoint-stage-2026-07-20.md) 与 [CreatorSeries 阶段实施记录](./creator-series-stage-2026-07-21.md)。声音模式仍需独立确认契约，不能直接从正文静默推断为长期资产。
