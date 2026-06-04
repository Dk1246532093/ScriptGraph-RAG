# ScriptGraph-RAG

基于知识图谱与RAG增强的AI小说转剧本系统

---

## 项目简介

本项目通过构建人物关系图谱和剧情记忆库，为大模型提供长期记忆能力，解决长篇小说转剧本时出现的：
- 人物设定遗忘
- 角色关系混乱
- 剧情前后矛盾
- 场景逻辑不一致

**核心流程**：小说上传 → 章节解析 → 知识图谱构建 → RAG知识库构建 → AI剧本生成 → YAML输出

---

## 技术栈

| 层级 | 技术 |
|-----|------|
| 前端 | Vue3 + TypeScript + Element Plus + Cytoscape.js |
| 后端 | FastAPI + Python |
| AI能力 | DeepSeek API / Qwen API |
| 知识图谱 | NetworkX + JSON |
| RAG | SentenceTransformers + FAISS |
| 文件处理 | python-docx + PyYAML |

---

## 项目结构

```
ScriptGraph-RAG/
├── backend/                    # FastAPI 后端服务
│   ├── app/
│   │   ├── api/               # API 路由层
│   │   │   └── __init__.py
│   │   ├── core/              # 核心配置
│   │   │   ├── __init__.py
│   │   │   └── config.py      # 项目配置（环境变量、路径、常量）
│   │   ├── models/            # 数据模型（Pydantic Schema）
│   │   │   └── __init__.py
│   │   ├── services/          # 业务逻辑层
│   │   │   └── __init__.py
│   │   └── utils/             # 工具函数
│   │       └── __init__.py
│   ├── storage/               # 数据持久化存储
│   │   ├── knowledge_graph/   # 知识图谱数据（graph.json）
│   │   ├── rag/               # RAG向量库（FAISS索引、chunks元数据）
│   │   ├── novels/            # 上传的小说原始文件（TXT/DOCX）
│   │   └── scripts/           # 生成的YAML剧本文件
│   ├── main.py                # FastAPI 应用入口
│   ├── requirements.txt       # Python 依赖包列表
│   └── .env.example           # 环境变量模板
│
├── frontend/                   # Vue3 前端应用
│   ├── src/
│   │   ├── api/               # Axios API 请求封装
│   │   │   └── index.ts
│   │   ├── components/        # 公共组件目录
│   │   ├── router/            # Vue Router 路由配置
│   │   │   └── index.ts
│   │   ├── stores/            # Pinia 状态管理
│   │   │   └── index.ts
│   │   ├── types/             # TypeScript 类型定义
│   │   │   └── index.ts       # 全局共享类型（Chapter、Character、Script等）
│   │   ├── utils/             # 工具函数
│   │   │   └── index.ts
│   │   ├── views/             # 页面视图组件
│   │   │   ├── HomeView.vue           # 首页
│   │   │   ├── UploadView.vue         # 小说上传页
│   │   │   ├── KnowledgeGraphView.vue # 知识图谱展示页
│   │   │   └── ScriptView.vue         # 剧本生成页
│   │   ├── App.vue            # 根组件
│   │   └── main.ts            # Vue 应用入口
│   ├── index.html             # HTML 模板
│   ├── package.json           # Node.js 依赖
│   ├── vite.config.ts         # Vite 构建配置
│   ├── tsconfig.json          # TypeScript 配置
│   └── tsconfig.node.json     # Node 端 TS 配置
│
└── 设计文档.md                 # 详细设计文档
```

---

## 文件夹作用详解

### backend/app/api/
存放 FastAPI 的路由定义，按功能模块划分：
- 小说上传接口
- 章节解析接口
- 知识图谱查询接口
- 剧本生成接口

### backend/app/core/
核心配置模块：
- **config.py**: 集中管理项目配置，包括数据库路径、API密钥、RAG参数等
- 使用 Pydantic Settings 实现环境变量加载和验证

### backend/app/models/
Pydantic 数据模型定义：
- 请求/响应 Schema
- 数据库模型
- 共享数据结构

### backend/app/services/
业务逻辑层：
- 小说解析服务
- 实体抽取服务
- 知识图谱构建服务
- RAG检索服务
- 剧本生成服务

### backend/app/utils/
通用工具函数：
- 文件读写
- 文本处理
- 数据转换

### backend/storage/
数据持久化目录，按类型分文件夹存储：
- **knowledge_graph/**: 知识图谱的节点和边数据（JSON格式）
- **rag/**: FAISS向量索引和Chunk摘要数据
- **novels/**: 用户上传的小说原始文件
- **scripts/**: 生成的YAML格式剧本

### frontend/src/types/
TypeScript 类型定义中心：
- 与后端API对接的数据接口
- 组件间共享的类型
- 知识图谱、剧本等核心数据结构定义

### frontend/src/views/
页面级组件，对应路由：
- **UploadView**: 小说文件上传、章节解析
- **KnowledgeGraphView**: 使用 Cytoscape.js 展示人物关系网络
- **ScriptView**: YAML剧本展示和预览

---

## 快速开始

### 后端启动

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 填入你的 API Key

# 启动服务
python main.py
```

后端服务默认运行在 http://localhost:8000

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务默认运行在 http://localhost:5173

---

## 环境变量配置

复制 `backend/.env.example` 为 `backend/.env`，并填写：

```env
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# 通义千问 API（备用）
QWEN_API_KEY=your_qwen_api_key
QWEN_API_BASE=https://dashscope.aliyuncs.com/api/v1
```

---

## 核心功能模块

| 模块 | 功能描述 |
|-----|---------|
| 小说上传 | 支持 TXT/DOCX 格式，自动保存到 storage/novels/ |
| 章节解析 | 自动识别"第一章"等标题进行切分 |
| 实体抽取 | 从文本中提取人物、地点、事件 |
| 知识图谱 | 构建人物关系网络，存储为 graph.json |
| RAG检索 | 文本分块、生成摘要、构建FAISS向量索引 |
| 剧本生成 | 结合知识图谱和RAG上下文调用LLM生成YAML剧本 |

---

## 数据流

```
小说文件 → 章节解析 → 实体抽取 → 知识图谱构建
                                      ↓
                              RAG知识库构建
                                      ↓
                         ┌────────────┴────────────┐
                         ↓                         ↓
                    知识图谱数据               RAG检索结果
                         └────────────┬────────────┘
                                      ↓
                              Prompt增强模块
                                      ↓
                              LLM剧本生成
                                      ↓
                              YAML剧本输出
```

---

## 开发计划

详见 [设计文档.md](设计文档.md) 第11章

---

## License

MIT
