# 音视频素材识别：小米全模态模型的接入（2026-09-18）

> 触发：用户要求「给项目中的素材识别分析的功能增加关于音视频相关的素材，需要连接
> 小米的 minov2.5-omni 全模态模型」。本文记录调研结论（含来源）、集成设计、隐私立场
> 与验证方式。

## 一、结论先说

- 用户说的模型是 **小米 MiMo 开放平台的 `mimo-v2.5`**（原生全模态：文本/图像/音频/视频 → 文本）。
- **`mimo-v2.5-omni` 不是官方 model id**：小米历史上确有 `mimo-v2-omni`，它已于
  **2026-06-30 下线**，官方给出的替代就是 `mimo-v2.5`。用户把两个名字缝在了一起；
  直接传 `mimo-v2.5-omni` 会被服务端拒绝。
- **OpenAI 兼容**：`POST https://api.xiaomimimo.com/v1/chat/completions`，
  `Authorization: Bearer <key>`（也支持 `api-key: <key>`）。因此不需要新协议栈。
- **不支持本地直传**：音频走 URL（≤100MB）或 base64（≤50MB）；视频走 URL（≤300MB）
  或 base64（≤50MB）。→ 我们这版用 base64 内联，因此设了 40MB 的素材上限；
  更大的文件需要先把素材放到公网可访问的地址（那是存储决策，不在这一步偷偷做）。

来源：MiMo 文档总索引 <https://mimo.mi.com/llms.txt>、模型列表
<https://mimo.mi.com/static/docs/quick-start/summary/model.md>、OpenAI Chat API
<https://mimo.mi.com/static/docs/api/chat/openai-api.md>、音频理解
<https://mimo.mi.com/static/docs/quick-start/usage-guide/multimodal-understanding/audio-understanding.md>、
视频理解 <https://mimo.mi.com/static/docs/quick-start/usage-guide/multimodal-understanding/video-understanding.md>、
下线表 <https://mimo.mi.com/static/docs/updates/deprecate.md>、定价
<https://mimo.mi.com/static/docs/price/pay-as-you-go.md>。

其他核对过的事实（都影响实现，逐条给依据）：

| 事实 | 对实现的影响 |
|---|---|
| 视频是**抽帧理解**（`fps` 默认 2、范围 0.1–10；`media_resolution` default/max） | 传 `fps`，默认 2；长视频 token 随 fps 线性增长 |
| 音轨单独计费，`mute=true` 可排除音频 token | 本版不排除（口播素材的价值就在声音） |
| `thinking` 默认开启且**非标准参数**，必须走 `extra_body` | 显式 `extra_body={"thinking": {"type": "disabled"}}`，降低延迟与成本 |
| 结构化输出只有 `json_object`，**没有 json_schema** | 不依赖 schema；识别结果要纯文本四段（含「未能确认」） |
| 限流 RPM 100 / TPM 10M，**账号级** | 用户手动触发（不是批量并发），够用 |
| 价格：`mimo-v2.5` 缓存命中 ¥0.02 / 未命中 ¥1.00 / 输出 ¥2.00 每百万 token | 一段 10 分钟音频 ≈ 3750 token，可忽略 |
| MiMo-V2.5 权重 MIT 开源，可自建 SGLang/vLLM 兜底 | 备选路径 |

## 二、集成设计（与产品既有约束对齐）

1. **素材类型**：`audio` / `video` 从第一天就在数据库 CHECK 里（`045` 迁移），只是
   Python 契约没暴露——**这一步没有动任何表约束**，只补了 `MaterialKind` 与校验。
2. **尺寸**：音视频限 40MB（官方 base64 上限 50MB，留出 base64 膨胀余量）；图文仍是 10MB。
3. **用户主动触发**：`POST /materials/{id}:analyze`。素材内容会离开本服务去外部模型，
   所以不自动跑；界面在按钮旁说明这一点。
4. **敏感素材不外发**：`privacy_level='sensitive'` 直接拒绝，并告诉用户先改级别。
5. **来源可见**：识别文本写回 `content_text`（下游项目素材读的就是它），
   来源写进新列 `analysis_json`（同一处 `_ensure_columns` 机制，纯加法）+
   `ai_traces_v2` 轨迹（`capability=omni_media`，`actual` 里含 `external_model_read`）。
   界面据此说明「这段文字是模型读出来的，可能听错」。
6. **不编造**：提示词要求四段输出，听不清/没提到一律写「未能确认」，并要求列出
   「无法确认」的部分；这与发布前检查、参考锚点的口径一致。
7. **未配置就给人话**：没有 key 时返回「音视频识别还没有开通：需要在服务端配置
   OMNI_API_KEY 并打开 OMNI_ENABLED」，不是 500、也不是静默无结果。

## 三、需要用户侧提供的东西

要让这条链路在线上真的跑起来，只有一件事：**在服务器 `.env` 里填 `OMNI_API_KEY` 并把
`OMNI_ENABLED=true`**（key 在 <https://platform.xiaomimimo.com> 申请，国内需实名；
不要把 key 贴进对话，直接写进服务器 `.env` 后重新部署即可）。在此之前界面仍可用，
点「识别内容」会得到上面那句可读的说明。

## 四、验证

- 后端 8 个契约测试：识别结果落库并标来源、**敏感素材绝不出网**（断言 stub 没被调用）、
  文本素材不需要识别、未配置时给可执行的话、载荷按官方格式拼（`input_audio` /
  `video_url` + `fps` + `media_resolution` + `extra_body.thinking`）、超限与未知格式
  用白名单拒绝、别人的素材读不到。
- 前端 2 个用例：已识别素材显示来源与「重新识别」；未识别素材显示「会发给外部模型」，
  点击调用识别接口。
