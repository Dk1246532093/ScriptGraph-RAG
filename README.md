# ScriptGraph-RAG

基于知识图谱与RAG增强的AI小说转剧本系统

---

## 项目演示

**在线观看（B站）**：

[【七牛云 × XEngineer 暑期实训营作品展示||小说转剧本】](https://www.bilibili.com/video/BV1qpEh6YEcg/)

---

## 项目简介

本项目通过构建人物关系图谱和剧情记忆库，为大模型提供长期记忆能力，解决长篇小说转剧本时出现的：
- 人物设定遗忘
- 角色关系混乱
- 剧情前后矛盾
- 场景逻辑不一致

**核心流程**：小说上传 → 章节解析 → 知识图谱构建 → AI剧本生成 → 在线编辑 → YAML/JSON/Fountain导出

---

## 技术栈

| 层级 | 技术 |
|-----|------|
| 前端 | Vue3 + TypeScript + Element Plus + Cytoscape.js |
| 后端 | FastAPI + Python |
| AI能力 | DeepSeek API |
| 知识图谱 | 大模型抽取 + JSON存储 |
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

### ✅ 知识图谱
- 基于大模型从小说原文抽取人物、地点、事件
- 可视化知识图谱展示（人物关系、地点关联）
- 图谱节点和关系的交互式浏览

### ✅ 剧本生成
- 流式生成剧本，实时显示进度
- 基于 DeepSeek API 智能分割场景
- 自动生成场景、Beats、台词
- 包含角色表情、动作、情绪、语气等详细信息

### ✅ 剧本编辑
- 在线编辑剧本内容
- 支持修改场景信息（标题、地点、概述）
- 支持修改 Beats（标题、主题、地点、氛围）
- 支持修改台词（角色、表情、动作、情绪、语气、台词内容）
- 支持添加/删除节拍和台词

### ✅ 历史记录
- 查看所有生成的剧本记录
- 查看知识图谱
- 查看剧本内容
- 在线编辑历史剧本
- 导出剧本

### ✅ 剧本导出
- 支持 YAML 格式导出
- 支持 JSON 格式导出
- 支持 Fountain 格式导出

---

## 项目结构

```
ScriptGraph-RAG/
├── backend/                    # FastAPI 后端服务
│   ├── app/
│   │   ├── api/               # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── novels.py      # 小说相关接口
│   │   │   └── scripts.py     # 剧本生成相关接口
│   │   ├── core/              # 核心配置
│   │   │   ├── __init__.py
│   │   │   └── config.py      # 项目配置
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── novel.py       # 小说数据模型
│   │   │   └── script.py      # 剧本数据模型
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── novel_service.py   # 小说服务
│   │   │   └── script_service.py  # 剧本服务
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       ├── txt_parser.py      # TXT解析器
│   │       ├── knowledge_graph.py # 知识图谱抽取
│   │       ├── scene_splitter.py  # 场景分割
│   │       ├── script_generator.py # 剧本生成
│   │       └── script_exporter.py  # 剧本导出
│   ├── storage/               # 数据持久化存储
│   │   ├── novels/            # 小说文件和元数据
│   │   └── result/            # 剧本生成结果
│   ├── main.py                # FastAPI 应用入口
│   ├── requirements.txt       # Python 依赖包列表
│   └── .env.example           # 环境变量模板
│
├── frontend/                   # Vue3 前端应用
│   ├── src/
│   │   ├── api/               # API 请求封装
│   │   │   ├── request.ts     # axios实例
│   │   │   ├── novel.ts       # 小说接口
│   │   │   └── script.ts      # 剧本接口
│   │   ├── components/        # 公共组件目录
│   │   │   └── KnowledgeGraph.vue  # 知识图谱组件
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
│   │   │   ├── ScriptView.vue         # 剧本生成页
│   │   │   ├── HistoryView.vue        # 历史记录页
│   │   │   └── ScriptEditorView.vue   # 剧本编辑页
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
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 填入你的 DeepSeek API Key

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

### 剧本接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | `/api/v1/scripts/generate/stream` | 流式生成剧本 |
| GET | `/api/v1/scripts/{script_id}` | 获取剧本详情 |
| GET | `/api/v1/scripts/{script_id}/script` | 获取剧本内容 |
| GET | `/api/v1/scripts/history/list` | 获取历史记录列表 |
| GET | `/api/v1/scripts/history/{script_id}` | 获取历史记录详情 |
| POST | `/api/v1/scripts/export` | 导出剧本（从前端数据） |
| GET | `/api/v1/scripts/{script_id}/export` | 导出剧本（从存储） |

---

## 环境变量配置

复制 `backend/.env.example` 为 `backend/.env`，并填写：

```env
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# 存储配置
STORAGE_DIR=storage
```

---


## 许可证

MIT License
