# TopicAI 内容线 · 交互架构图

> 依据：`content-line-interaction-map-v1.md` + v1.1 审查补丁  
> 节点：页面 / 浮层 / 关键动作

---

## 1. 全局导航与信息架构

```mermaid
flowchart TB
  subgraph shell [全局壳]
    Side[侧栏 8 项]
    Top[顶栏 标题 + 唯一主 CTA]
    Ball[悬浮球]
  end

  Side --> Today[今日]
  Side --> Content[内容]
  Side --> Review[周复盘]
  Side --> Growth[成长]
  Side --> Path[路径]
  Side --> Mat[素材]
  Side --> Me[我的]
  Side --> Settings[设置]

  Ball --> GAI[全局 AI 面板]
  GAI -.->|设置入口| Settings
  Me -->|打开设置| Settings
```

---

## 2. 主链：一条内容（轻 → 重）

```mermaid
flowchart LR
  A[灵感一句话] --> B{快速开始}
  B -->|只记下来| C[内容 · 想发的]
  B -->|立成内容| D[项目屏]
  C -->|觉得要做| D
  D --> E[对话 + 产物]
  E --> F[确认卡]
  F -->|同意| G[登记发布]
  F -->|改| E
  F -->|否决| E2[改稿 / 换建议 / 搁置]
  E2 --> E
  G --> H[对账 1-2 数或跳过]
  H --> I[准 / 偏]
  I --> J[写回路径 · 人确认]
```

---

## 3. 今日 → 各锚点（跳转带提示）

```mermaid
flowchart TB
  T[今日待决]
  T -->|候选 · 去处理| P1[项目 · 稿+确认卡<br/>提示：已打开确认候选]
  T -->|公开 · 去处理| P2[项目 · 确认卡<br/>提示：公开范围]
  T -->|预产 · 去审| P3[项目 · 视频包]
  T -->|对账| R[周复盘 · 欠对账并聚焦]
  T -->|路径提醒| PA[路径]
  T -->|去素材| M[素材]
```

---

## 4. 项目屏内部

```mermaid
flowchart TB
  subgraph left [左 · 对话 项目助手]
    Chat[消息流]
    Dec[确认卡 同意/改/否决]
    Input[输入 发送]
  end
  subgraph right [右 · 产物]
    Tab1[稿 · 就地改]
    Tab2[发布包 · 一键修]
    Tab3[视频包 · 匹配/粗拼]
    Tab4[bet / 对账]
  end
  Stage[阶段条 · 只展开]
  Cfg[本条助手设置] --> Settings
  Chat --> Tab1
  Dec -->|同意| Next[推进状态]
  Dec -->|否决| Choice[改稿/换建议/搁置]
  Input --> Chat
```

---

## 5. 全局 AI（灵感 + 操控）

```mermaid
flowchart TB
  Ball[悬浮球] --> Panel[全局 AI 面板]
  Panel --> Cap[速记一句话]
  Cap --> Want[内容 · 想发的]
  Panel --> Ctrl[操控指令]
  Ctrl --> Preview[预览 将执行：…]
  Preview -->|确认| Do[跳页 / 新建 / 对账 / 改设置]
  Preview -->|取消| Panel
  Panel --> Open[打开某条内容]
  Open --> Proj[项目屏 · 对话区]
  style Proj stroke:#c98a4b
```

**全局 AI 不做**：改稿正文、代点确认卡、代四决策（发布/公开/长期经验/删除）。

---

## 6. 双 AI 职责

```mermaid
flowchart LR
  subgraph G [全局 AI]
    G1[速记]
    G2[跳转/代办]
    G3[解释下一步]
    G4[改设置 预览后]
  end
  subgraph P [项目助手]
    P1[改稿/重写]
    P2[出确认卡]
    P3[只谈这一条]
  end
  G1 --> Want[想发的]
  G2 --> Pages[各页]
  P1 --> Draft[产物稿]
  P2 --> Human[你拍板]
```

---

## 7. 设置页结构

```mermaid
flowchart TB
  S[设置 整页]
  S --> S1[产品与创作]
  S --> S2[全局 AI 名称头像 agent.md 模型 操控范围]
  S --> S3[项目助手 名称头像 agent.md 语气 去AI味]
  S --> S4[记忆 路径/公式/写入方式]
  S --> S5[隐私 导出 删除]
  S2 -.即改即存.-> V1[已保存]
  S3 -.即改即存.-> V1
```

---

## 8. 状态机（条目）

```mermaid
stateDiagram-v2
  [*] --> 想发的: 速记/快速开始
  想发的 --> 在途: 立成内容
  在途 --> 待确认: 稿就绪
  待确认 --> 在途: 否决后改稿
  待确认 --> 已发: 确认+登记
  已发 --> 待对账: T+N
  待对账 --> 已对账: 记下/跳过
  已对账 --> 已沉淀: 收公式
  想发的 --> [*] : 搁置/删除
```

---

## 9. 错误 / 空 / 载

```mermaid
flowchart LR
  L[loading 骨架] --> E{结果}
  E -->|空| Empty[为什么空 + 下一步]
  E -->|成功| Data[数据]
  E -->|失败| Err[原因 + 重试 不清旧数据]
```

---

## 10. 入口对照（谁从哪进）

| 要做的事 | 主入口 | 备入口 |
|---|---|---|
| 记灵感 | 全局 AI / 快速开始 | 收件箱（素材） |
| 写一条 | 内容 · 立成内容 | 今日 · 去处理 |
| 改稿 | 项目屏 | — |
| 拍板 | 确认卡 | 全局 AI 只能「打开」 |
| 对账 | 周复盘 | 今日 · 欠对账 |
| 调路径 | 路径 | 偏离提醒 |
| 改 AI | 设置 · 全局/项目 | 项目屏「本条助手设置」 |
