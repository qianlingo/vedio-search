# 夸克网盘资源搜索工具

自动从 Google/Bing 搜索结果及二级页面中挖掘夸克网盘分享资源，流式展示搜索进度和资源详情。

## 预览

![screenshot](https://via.placeholder.com/800x480/fafbfc/2563eb?text=Quark+Resource+Search)

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python FastAPI + Playwright（Chromium 无头浏览器） |
| 前端 | Vue 3 + Vite |
| 通信 | SSE (Server-Sent Events) 流式推送 |

## 搜索流程

```
用户输入关键词
  ├─ ❶ Google 搜索 "{关键词} 夸克网盘"
  │     └─ 失败自动回退 Bing
  ├─ ❷ 从搜索结果中提取 quark.cn 链接
  │     └─ 同时收集非夸克页面链接（最多 8 个）
  ├─ ❸ 二级挖掘：访问非夸克页面，寻找隐藏的 quark.cn 链接
  ├─ ❹ 合并去重，逐个访问每个夸克链接
  │     ├─ 提取资源标题、文件列表、提取码
  │     └─ 凑满 6 个有效资源自动停止
  └─ ❺ SSE 实时推送进度到前端
```

## 项目结构

```
search/
├── backend/
│   ├── main.py              # FastAPI + Playwright 搜索引擎
│   └── requirements.txt     # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── App.vue          # 主组件（搜索界面 + 结果展示）
│   │   └── main.js          # Vue 入口
│   ├── index.html
│   ├── vite.config.js       # Vite 配置（含 API 代理）
│   └── package.json
├── start.bat                # Windows 一键启动
└── README.md
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Playwright Chromium 浏览器

### 安装

```bash
# 后端
cd backend
python -m venv venv
venv/Scripts/pip install -r requirements.txt   # Windows
venv/bin/pip install -r requirements.txt       # macOS/Linux
venv/Scripts/playwright install chromium       # 安装浏览器

# 前端
cd frontend
npm install
```

### 启动

**Windows（一键）:**

双击 `start.bat`

**手动分别启动:**

```bash
# 终端 1 — 后端（端口 8000）
cd backend
venv/Scripts/python.exe main.py

# 终端 2 — 前端（端口 5173）
cd frontend
npx vite --host 0.0.0.0
```

打开浏览器访问 `http://localhost:5173`

## 功能特性

- **多引擎搜索**: Google 优先，被拦截自动回退 Bing，页面标识搜索引擎
- **二级页面挖掘**: 不只搜 `quark.cn` 链接，还会访问普通结果页探寻隐藏的夸克链接
- **实时进度**: SSE 流式推送，搜索步骤可展开查看详情
- **站点时间线**: 每个访问的夸克链接独立展示，节点颜色标识状态（访问中/成功/失败）
- **搜索汇总**: 完成后展示链接数、资源数、文件条目、耗时
- **资源提取**: 自动提取页面标题、文件列表、提取码
- **提前停止**: 收集到 6 个有效资源后自动结束

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/search?query=xxx` | GET | SSE 流式搜索 |
| `/api/search` | POST | POST 方式搜索（同上） |
| `/api/health` | GET | 健康检查 |

### SSE 事件类型

| type | 说明 |
|------|------|
| `progress` | 进度信息（包含 engine 字段标识 Google/Bing） |
| `link_found` | 发现 quark.cn 链接（source: "secondary" 表示二级挖掘） |
| `resource_found` | 提取到资源（含标题、文件列表、提取码） |
| `error` | 出错 |
| `complete` | 搜索完成（含汇总数据） |
