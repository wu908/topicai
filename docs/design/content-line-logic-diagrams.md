# TopicAI 内容线 · 逻辑图（确认用）

> 配套：业务 v1.1 · UX/UI v1 · 待确认 HTML 原型  
> Pencil 桌面端当前未连接，本稿先用矢量逻辑图 + HTML 原型；你打开 Pencil 后可再导入画布精修。

---

## 1. 产品三维与主闭环

```mermaid
flowchart TB
  subgraph path [路径 Path]
    P1[我是谁/发什么]
    P2[红线/节奏]
    P3[对标锚]
    P4[公式笔记]
  end
  subgraph content [内容 Content]
    C1[想发的]
    C2[对话成稿]
    C3[发前门]
    C4[发布登记]
  end
  subgraph judge [判断 Judgment]
    J1[盲 bet]
    J2[对账 准/偏]
    J3[写回路径 人确认]
  end
  path --> content --> judge --> path
```

---

## 2. 一条内容（条级状态机）

```mermaid
stateDiagram-v2
  [*] --> idea: 说一句/捕获
  idea --> angle: AI 深挖+你点头
  angle --> drafting: 起草/人话化
  drafting --> ready_gate: 你改完
  ready_gate --> bet_locked: 发前检查+半句 bet
  bet_locked --> published: 你登记已发
  published --> retro_due: T+N
  retro_due --> retro_done: 1-2 数或跳过
  retro_done --> settled: 收/不收经验
  drafting --> shots: 若为视频
  shots --> assembling: 匹配素材+粗拼
  assembling --> ready_gate
```

---

## 3. 人机分工（谁干什么）

```mermaid
flowchart LR
  IN[人: 输入想法/素材/对账数] --> AGENT[Agent 四层技能]
  AGENT --> OUT[产物: 稿/检查/视频包]
  OUT --> DEC[人: 点头/改字/否决]
  DEC --> MEM[记忆/公式 提案]
  MEM -->|人确认| AGENT
```

| 人 | AI |
|---|---|
| 输入、拍板、改字、收/拒经验 | 深挖、起草、人话化、匹配、检查、对账摘要、沉淀提议 |

---

## 4. 页面信息架构（v1.1：保留成长与周复盘）

```mermaid
flowchart TB
  T[今日: 待决队列+快速开始] -->|进条| PS[项目屏]
  C[内容: 想发/在途/已发] --> PS
  PS --> CH[左对话]
  PS --> AR[右产物: 稿/发布包/视频包/bet]
  R[周复盘: 判断vs实际+准偏+公式] --> PS
  G[成长: 能力台帐+里程碑+信任] --> CH
  PA[路径: 画像/对标/公式/探索] --> CH
  M[素材] --> AR
  ME[我的] --> PA
```

**一级导航 7 项（2026-10-11 你确认保留成长/周复盘）**  
今日 · 内容 · **周复盘** · **成长** · 路径 · 素材 · 我的

---

## 5. 确认卡（全站唯一）

```mermaid
flowchart LR
  A[AI 提议] --> B{确认卡}
  B -->|同意| C[推进状态]
  B -->|改| D[改后推进]
  B -->|否决| E[记录原因 不死路]
  C --> F[今日队列消化]
```

类型：事实/意图/发布/长期经验 —— 同一 UI 形态。

---

## 6. 七步主链（图文）

```mermaid
flowchart LR
  S1[想发] --> S2[成稿+人话化] --> S3[发前门] --> S4[登记发布] --> S5[对账] --> S6[准/偏] --> S7[写回路径]
```

---

## 7. 对标输入流

```mermaid
flowchart LR
  A[粘贴样本/链接] --> B[自动读 选题/结构/读者]
  B --> C[逐条确认]
  C --> D[写入路径]
  D --> E[影响选题/成稿/检查]
```

---

## 8. 待决队列数据源

```mermaid
flowchart TB
  Q[今日待决] --> Q1[等你定的确认卡]
  Q --> Q2[欠对账]
  Q --> Q3[路径提醒]
  Q --> Q4[AI 后台预产可选]
```

---

（HTML 交互原型见同目录 `content-line-prototype.html`）
