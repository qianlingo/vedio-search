# 夸克网盘资源搜索工具

自动从 Google/Bing/百度 搜索结果及二级页面中挖掘夸克网盘分享资源，流式展示搜索进度和资源详情。支持电视剧集数智能比对。

## 在线演示

> **[点击体验演示模式](https://qianlingo.github.io/vedio-search/)**

演示模式使用模拟数据展示完整搜索流程效果，无需后端。实际使用请在本地启动后端服务。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python FastAPI + Playwright（Chromium 无头浏览器） |
| 前端 | Vue 3 + Vite |
| 通信 | SSE (Server-Sent Events) 流式推送 |

## 搜索流程

```
用户输入关键词
  ├─ ❶ 剧集检测（豆瓣 → Google → Bing → 爱奇艺 → 腾讯视频 → 优酷）
  ├─ ❷ 多引擎搜索 "{关键词} 夸克网盘"
  │     ├─ Google（CAPTCHA 检测，被拦截自动切换）
  │     ├─ Bing（重定向链接解码）
  │     └─ 百度（备用）
  ├─ ❸ 二级挖掘：访问非夸克页面，寻找隐藏的 quark.cn 链接
  ├─ ❹ 合并去重，逐个访问每个夸克链接
  │     ├─ 提取资源标题、文件列表、提取码
  │     ├─ 剧集比对（夸克集数 vs 官方集数）
  │     └─ 凑满 6 个有效资源或 6 秒无新资源自动停止
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
│   │   ├── App.vue          # 主组件（搜索界面 + 总览页面）
│   │   └── main.js          # Vue 入口
│   ├── index.html
│   ├── vite.config.js       # Vite 配置
│   └── package.json
├── docs/                    # GitHub Pages 静态构建（演示模式）
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

### 部署演示站到 GitHub Pages

```bash
cd frontend
npx vite build           # 构建到 dist/
cp -r dist/* ../docs/    # 复制到 docs 目录
touch ../docs/.nojekyll  # 禁用 Jekyll 处理
git add docs/ && git commit -m "update demo site" && git push
```

在 GitHub 仓库 Settings → Pages → Source 选择 `main` 分支 `/docs` 目录。

## 功能特性

- **多引擎搜索**: Google → Bing → 百度 级联搜索，自动检测 CAPTCHA 并切换
- **二级页面挖掘**: 不只搜 `quark.cn` 链接，还会访问普通结果页探寻隐藏的夸克链接
- **剧集检测与比对**: 自动检测关键词是否为电视剧，获取官方集数，与夸克资源比对完整性
- **实时进度**: SSE 流式推送，搜索步骤实时展示
- **总览页面**: 搜索完成后展示统计卡片（资源数、链接数、文件数、耗时）
- **自动完成**: 找到资源后 6 秒无新资源自动完成，支持手动立即完成
- **资源提取**: 自动提取页面标题、文件列表、提取码
- **提前停止**: 收集到 6 个有效资源后自动结束
- **演示模式**: GitHub Pages 静态站点，无需后端即可体验完整流程

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/search?query=xxx` | GET | SSE 流式搜索 |
| `/api/search` | POST | POST 方式搜索（同上） |
| `/api/health` | GET | 健康检查 |

### SSE 事件类型

| type | 说明 |
|------|------|
| `progress` | 进度信息（包含 engine 字段标识搜索引擎） |
| `series_detected` | 检测到电视剧信息（剧名、总集数、来源） |
| `link_found` | 发现 quark.cn 链接（source: "secondary" 表示二级挖掘） |
| `resource_found` | 提取到资源（含标题、文件列表、提取码、剧集比对结果） |
| `error` | 出错 |
| `complete` | 搜索完成（含汇总数据和 series_info） |
