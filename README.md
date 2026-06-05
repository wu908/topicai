# TopicAI v4.0 "Air Pro"

> AI 智能选题推荐 Agent — 面向内容创作者的全流程 AI 助手

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://python.org) [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com) [![React 19](https://img.shields.io/badge/React-19-blue)](https://react.dev) [![Tests](https://img.shields.io/badge/Tests-327%20passed-brightgreen)](#)

---

## 功能特性

| 功能模块 | 说明 |
|--------|------|
| **智能选题推荐** | 基于赛道 + 创作画像 + 热点数据的多维推荐 |
| **爆款拆解** | LLM 分析爆款内容结构（支持文本/图片/视频） |
| **想法推进** | 把粗糙想法扩展为完整内容创作方案 |
| **标题优化** | 多维评分 + 爆款标题公式生成候选 |
| **赛道诊断** | 评估赛道竞争度、机会窗、红利期预警 |
| **创作画像** | 基于行为动态学习的个人创作风格画像 |
| **效果复盘** | 发布后数据分析 + 盲预测归因 |
| **发布时间** | 基于平台 + 赛道的最优发布时间建议 |

---

## 快速启动

### 前提条件

- Python 3.12+
- Node.js 22+
- DeepSeek API Key（必须）

### 方式一：本地开发（推荐）

**后端**

```bash
cd backend

# 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 DEEPSEEK_API_KEY

# 创建虚拟环境 & 安装依赖
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
pip install "bcrypt==4.0.1" "pydantic[email]"

# 启动后端
uvicorn "main:create_app" --factory --host 127.0.0.1 --port 8000 --reload
```

API 文档：http://localhost:8000/docs

**前端**

```bash
cd frontend
npm install
npm run dev
```

应用地址：http://localhost:5173

### 方式二：Docker 一键部署

```bash
cp backend/.env.example .env
# 编辑 .env 填入 API Keys

docker compose up -d
```

- 后端 API：http://localhost:8000
- 前端界面：http://localhost
- API 文档：http://localhost:8000/docs

---

## 技术架构

### 后端（FastAPI）

```
backend/
├── app/
│   ├── api/v1/            # 21 个 REST API 端点
│   ├── chains/             # LangChain 处理链
│   ├── content_analyzers/  # 文本/图像内容分析器
│   ├── core/               # LLM 客户端、JWT 认证、数据库
│   ├── data_sources/       # TianAPI + B站 + LLM 模拟 + 预置基准
│   ├── middleware/         # 认证中间件、速率限制、监控
│   ├── models/             # Pydantic 数据模型
│   ├── prompts/            # 版本化 Prompt 文件
│   ├── services/           # 业务逻辑层（17 个服务）
│   └── tasks/              # 定时任务
├── tests/                  # 274 条 pytest 测试用例
├── main.py                 # FastAPI 工厂函数入口
└── requirements.txt
```

### 前端（React + MUI）

```
frontend/src/
├── components/
│   ├── layout/             # AppLayout + Sidebar + Header
│   ├── common/             # LoadingCard, EmptyState, ConfidenceBadge
│   ├── feedback/           # ThumbFeedback + FeedbackDialog
│   └── ai-badge/           # AICreatedBadge + AIDegradedNotice
├── pages/                  # 10 个功能页面
├── services/api/           # Axios + JWT 自动刷新（11 个 API 模块）
├── store/                  # Zustand 状态管理（auth/profile/app）
├── hooks/                  # useAuth/useApi/useRateLimit/useFeedback
└── e2e/                    # Playwright E2E 测试（8 条）
└── types/                  # TypeScript 类型定义
```

### LLM 调度（4 层）

| 层级 | 模型 | 用途 |
|------|------|------|
| 默认推理 | `deepseek-v4-flash` | 所有常规推理任务，2500 并发 |
| 深度分析 | `deepseek-v4-pro` | 复杂分析 + 思维链，500 并发 |
| 热备 | `qwen-plus` | DeepSeek 不可用时自动切换 |
| 视觉 | `glm-5v-turbo` | 图片/视频内容分析（200K上下文） |

---

## 环境变量

| 变量 | 必须 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek V4 API Key |
| `JWT_SECRET_KEY` | ✅（生产） | JWT 签名密钥，≥32位随机字符串 |
| `DASHSCOPE_API_KEY` | 可选 | Qwen 热备 API Key |
| `ZHIPU_API_KEY` | 可选 | GLM-5V-Turbo 视觉模型 |
| `TIANAPI_KEY` | 可选 | 热搜数据（免费 100 次/天） |
| `SENTRY_DSN` | 可选 | 错误追踪（Sentry） |
| `LANGFUSE_PUBLIC_KEY` | 可选 | LLM 链路追踪（LangFuse） |
| `POSTHOG_API_KEY` | 可选 | 用户行为分析（PostHog） |

详见 `backend/.env.example`

---

## 开发测试

```bash
# 运行后端测试（274 条）
cd backend
source .venv/Scripts/activate
pytest tests/ -v

# 运行前端类型检查 & 构建
cd frontend
npx tsc --noEmit
npm run build

# 启动前端开发服务
npm run dev
```

---

## API 端点总览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/refresh` | POST | 刷新 Token |
| `/api/v1/profiles/onboarding` | POST | 创作画像初始化 |
| `/api/v1/profiles/me` | GET/PUT | 获取/更新画像 |
| `/api/v1/topics/recommend` | GET | 选题推荐 |
| `/api/v1/viral/analyze` | POST | 爆款拆解 |
| `/api/v1/ideas/boost` | POST | 想法推进 |
| `/api/v1/titles/optimize` | POST | 标题优化 |
| `/api/v1/tracks/diagnose` | POST | 赛道诊断 |
| `/api/v1/publish/suggest` | POST | 发布时间建议 |
| `/api/v1/feedback` | POST | 提交反馈 |

---

## 数据安全

- 用户内容 90 天自动清理（`expires_at` 字段）
- JWT 认证（无 Cookie），Token 30 分钟过期 + Refresh Token 7 天
- AI 调用速率限制：20 次/天（免费层）
- AI 内容标识：所有 AI 输出含 `confidence` + `data_source` + `model_version`

---

## License

MIT
