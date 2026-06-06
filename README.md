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

## 已实现功能

### ✅ 书架管理
- 上传 TXT 格式小说文件
- 自动检测文件编码（UTF-8/GBK/GB2312）
- 智能解析章节（支持"第X章"、"第一章"等格式）
- 小说列表展示和删除

### ✅ 小说阅读
- 章节列表导航
- 章节内容阅读
- 小说基本信息展示

### 🚧 知识图谱（开发中）
- 人物关系图谱构建
- 剧情时间线展示

### 🚧 剧本生成（开发中）
- 选择章节范围生成剧本
- YAML格式剧本输出
- 在线编辑剧本

---

## 项目结构

```
ScriptGraph-RAG/
├── backend/                    # FastAPI 后端服务
│   ├── app/
│   │   ├── api/               # API 路由层
│   │   │   ├── __init__.py
│   │   │   └── novels.py      # 小说相关接口
│   │   ├── core/              # 核心配置
│   │   │   ├── __init__.py
│   │   │   └── config.py      # 项目配置
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   └── novel.py       # 小说数据模型
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   └── novel_service.py  # 小说服务
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       └── txt_parser.py  # TXT解析器
│   ├── storage/               # 数据持久化存储
│   │   └── novels/            # 小说文件和元数据
│   ├── main.py                # FastAPI 应用入口
│   ├── requirements.txt       # Python 依赖包列表
│   └── .env.example           # 环境变量模板
│
├── frontend/                   # Vue3 前端应用
│   ├── src/
│   │   ├── api/               # API 请求封装
│   │   │   ├── request.ts     # axios实例
│   │   │   └── novel.ts       # 小说接口
│   │   ├── components/        # 公共组件目录
│   │   ├── router/            # Vue Router 路由配置
│   │   │   └── index.ts
│   │   ├── stores/            # Pinia 状态管理
│   │   │   └── index.ts
│   │   ├── types/             # TypeScript 类型定义
│   │   │   └── index.ts
│   │   ├── utils/             # 工具函数
│   │   │   └── index.ts
│   │   ├── views/             # 页面视图组件
│   │   │   ├── HomeView.vue           # 首页
│   │   │   ├── BookshelfView.vue      # 书架页（上传/列表）
│   │   │   ├── NovelDetailView.vue    # 小说详情页
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
└── 原型图/                     # UI原型设计
    └── index.html             # 原型图预览
```

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

## API 接口

### 小说接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/v1/novels` | 获取小说列表 |
| POST | `/api/v1/novels/upload` | 上传小说文件 |
| GET | `/api/v1/novels/{id}` | 获取小说详情 |
| DELETE | `/api/v1/novels/{id}` | 删除小说 |
| GET | `/api/v1/novels/{id}/chapters` | 获取章节列表 |
| GET | `/api/v1/novels/{id}/chapters/{chapter_id}` | 获取章节内容 |

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

## 开发计划

- [x] 书架管理（上传/列表/删除）
- [x] TXT 文件解析（多编码支持）
- [x] 章节智能识别
- [x] 小说阅读器
- [ ] 知识图谱构建
- [ ] RAG 知识库
- [ ] AI 剧本生成
- [ ] YAML 剧本编辑

---

## 许可证

MIT License
