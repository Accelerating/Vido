# Vido

一个自托管的视频下载 Web 服务，基于 yt-dlp 支持视频下载，提供离线播放、下载任务管理、Cookie 配置管理以及多用户认证功能。

## 功能特性

- **视频下载** — 提交 YouTube 链接，通过 yt-dlp 下载
- **格式选择** — 下载前可选择视频分辨率和格式
- **离线播放** — 在浏览器中直接流式播放已下载的视频
- **任务管理** — 追踪下载进度、取消任务、查看日志
- **Cookie 配置** — 导入 Netscape 格式的 Cookie（支持文件上传或粘贴），用于需要登录的下载
- **多用户** — 支持注册/登录，基于 Cookie 的认证方式，每个用户的任务和文件相互隔离
- **国际化** — 界面支持中文和英文

## 环境依赖

### 系统要求

- **Python >= 3.13**
- **Node.js >= 24**（用于构建前端）
- **pnpm**（通过 corepack 启用或全局安装）
- **uv**（Python 包管理器）

### 后端依赖

| 依赖 | 用途 |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Web 框架 |
| [uvicorn](https://www.uvicorn.org/) | ASGI 服务器 |
| [bcrypt](https://pypi.org/project/bcrypt/) | 密码哈希 |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 视频下载引擎 |
| [python-multipart](https://pypi.org/project/python-multipart/) | 表单/文件上传支持 |

### 前端依赖

| 依赖 | 用途 |
|---|---|
| [React 19](https://react.dev/) | UI 框架 |
| [react-router v7](https://reactrouter.com/) | 客户端路由 |
| [TanStack Query](https://tanstack.com/query) | 服务端状态管理 |
| [Tailwind CSS v4](https://tailwindcss.com/) | 样式方案 |
| [shadcn/ui](https://ui.shadcn.com/) | UI 组件库 |
| [Vite](https://vitejs.dev/) | 构建工具 |

## 快速开始

`deploy.sh` 一键完成所有部署步骤——安装系统依赖、克隆仓库、构建前端、启动服务。

首先，在 `deploy.sh` 顶部填好你的 GitHub 仓库地址：

```bash
REPO_URL="<your-github-repo-url>"   # TODO: 填入你的仓库地址
```

然后运行：

```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动完成以下步骤：

1. 安装 nvm + Node.js 24、pnpm、uv、yt-dlp
2. 克隆仓库（若已存在则 `git pull` 更新）
3. `pnpm install && pnpm build` 构建前端
4. `uv sync` 安装后端依赖
5. 启动服务，访问 `http://localhost:8000`

## 开发指南

### 后端开发服务器

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端开发服务器

```bash
cd frontend
pnpm dev
```

Vite 开发服务器运行在 `http://localhost:5173`，会自动将 `/api` 请求代理到后端的 `127.0.0.1:8000`。

### 运行测试

```bash
cd backend
uv run pytest -v
```

测试使用独立的数据库（`test_vido.db`），通过 `VIDO_TEST=1` 环境变量切换，该变量由 `conftest.py` 自动设置。

## 架构说明

Vido 作为**单个 FastAPI 进程**运行，同时提供 REST API 和构建后的 React 前端静态文件，无需额外的 Web 服务器（如 nginx）。

- **数据库：** 使用 SQLite，采用线程本地连接（thread-local）。首次启动时会在 `backend/vido.db` 创建数据库文件。
- **认证：** 基于 Cookie 的认证方式，UUID 令牌存储在 `auth_tokens` 表中，Cookie 设置为 `httponly`。
- **下载引擎：** yt-dlp 作为子进程运行，通过 `asyncio.create_subprocess_exec` 调用。下载文件存储在 `backend/downloads/{user_id}/{task_id}/`，日志存储在 `backend/logs/{user_id}/{task_id}.log`。
- **Cookie 存储：** Cookie 文件内容存储在磁盘上 `backend/cookies/{user_id}/{profile_id}.txt`，元数据存储在 SQLite 的 `cookie_profiles` 表中。

### 任务生命周期

```
pending → downloading → completed
                      → failed
```

服务重启时，所有卡在 `downloading` 状态的任务会自动标记为 `failed`，错误信息为 "Server restarted"。

### 目录结构

```
Vido/
├── backend/
│   ├── app/            # FastAPI 应用
│   │   ├── auth.py     # 注册、登录、登出
│   │   ├── tasks.py    # 下载任务 CRUD + yt-dlp 子进程调用
│   │   ├── videos.py   # 视频列表、播放、删除
│   │   ├── cookies.py  # Cookie 配置管理
│   │   ├── stats.py    # 使用统计
│   │   ├── system.py   # yt-dlp 版本、系统信息
│   │   ├── database.py # SQLite 连接管理
│   │   ├── config.py   # 路径和常量
│   │   └── main.py     # 应用工厂与路由注册
│   ├── tests/           # pytest 测试套件
│   ├── static/          # 前端构建产物
│   ├── downloads/       # 下载的视频文件
│   ├── cookies/         # Cookie 配置文件
│   ├── logs/            # 下载任务日志
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── api/         # API 客户端
│       ├── components/  # 可复用 UI 组件
│       ├── i18n/        # 国际化翻译（中文/英文）
│       ├── lib/         # 工具函数
│       └── pages/       # 路由页面
├── deploy.sh            # 一键部署脚本
└── README.md
```
