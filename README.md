# Transparent Proxy Gateway

基于 **Django + Django-Ninja + ASGI + Vue3** 的透明 HTTP 反向代理网关：动态注册路由、流式转发、可视化管理，行为类似 nginx 的**前缀转发**（非 path rewrite）。

## 特性

- **前缀转发**：`/account` → `http://upstream:8000`，访问 `/account/login` 转发为 `http://upstream:8000/account/login`
- **通配符路由**：`/*`、`/robot/*`；每个通配作用域仅允许一条上游
- **最长前缀匹配**：精确前缀优先于同作用域通配
- **全异步流式**：`httpx.AsyncClient` + `StreamingHttpResponse`，支持大文件与 chunked
- **透传**：Headers / Cookies / Body / Query（过滤 Hop-by-Hop 头）
- **WebSocket**：与 HTTP 同前缀规则双向转发（`ws`/`wss`）；管理台 `/ws/logs/` 除外
- **响应改写**：`Set-Cookie` Path、`Location`（301/302 等）、`Referer`/`Origin`
- **管理台**：路由、节点健康、请求日志、统计图表、实时日志、系统配置（**无需登录**）
- **HTTPS 上游**：`PROXY_SSL_VERIFY` / 自定义 CA
- **PyPI 包**：`transparent-proxy-gateway`，可嵌入任意 Django 项目

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端包 | Django 5+、Django-Ninja、httpx、Channels、loguru |
| 演示项目 | Daphne、WhiteNoise、Vue 管理台（`django_proxy/` + `frontend/`，非 PyPI 包） |
| 前端 | Vue 3、Vite、Element Plus、ECharts |

## 快速开始

### 1. 安装与迁移

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt   # 含 editable 安装 transparent-proxy-gateway
python manage.py migrate
python manage.py init_gateway
# 无需 createsuperuser（控制台无登录）；仅使用 Django Admin 时才需要
```

### 2. 启动

```bash
python manage.py runserver 8000
# 或: daphne -b 0.0.0.0 -p 8000 django_proxy.asgi:application
```

### 3. 前端（可选）

```bash
cd frontend && npm install && npm run build
# 开发: npm run dev  → http://localhost:5173，/api 代理到 8000
```

### 4. 访问

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/ | 管理台（直接进入，无登录） |
| http://127.0.0.1:8000/api/docs | OpenAPI 文档 |
| http://127.0.0.1:8000/{prefix}/... | 已注册前缀的代理流量 |

**示例：** 前缀 `/test` → `http://127.0.0.1:8888`  
访问 `http://127.0.0.1:8000/test/page` → 转发 `http://127.0.0.1:8888/test/page`

## 配置

```bash
cp .env.example .env
```

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
LOG_LEVEL=INFO

PROXY_FORWARD_MODE=stream
PROXY_SSL_VERIFY=true
# PROXY_SSL_VERIFY=false
HEALTH_CHECK_INTERVAL=30
REDIS_URL=

# 可选：PostgreSQL / MySQL（需 pip install -e ".[postgres]" 或 ".[mysql]"）
# DATABASE_URL=postgresql://user:pass@localhost:5432/gateway
```

## 数据库

**网关包不管理数据库连接**，仅使用宿主项目 `settings.DATABASES` 中的默认库。

本演示仓库在 `django_proxy/settings.py` 中配置数据库（支持 `DATABASE_URL` / `DJANGO_DB_*`），详见 [docs/项目文档.md](docs/项目文档.md) 第 9 节。

```bash
python manage.py migrate transparent_proxy_gateway
```

## 架构

```
浏览器 → Daphne (ASGI)
           ├─ /api/*     → Django-Ninja 管理 API（网关包）
           ├─ /routes …  → Vue SPA（仅演示项目 django_proxy）
           └─ /{prefix}  → proxy_view → httpx 流式 → 上游
```

PyPI 包**不包含** `NinjaAPI` 与前端 SPA；嵌入项目自建 `NinjaAPI` 并挂载网关 `Router`，再加 `build_proxy_catchall()`。

## 管理 API（无需 Token）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/routes` | 路由 CRUD |
| GET | `/api/nodes` | 节点健康 |
| POST | `/api/nodes/check` | 立即健康检查 |
| GET | `/api/logs` | 请求日志 |
| GET | `/api/logs/stats/*` | 统计聚合 |
| GET/PUT | `/api/config` | 系统配置 |

## 项目结构

```
transparent_proxy_gateway/   # PyPI 包源码
django_proxy/                # 演示用 Django 项目
frontend/                    # Vue 管理台
docs/                        # 项目文档.md、PACKAGING.md
pyproject.toml
```

## PyPI 集成

```bash
pip install transparent-proxy-gateway
```

详见 [docs/PACKAGING.md](docs/PACKAGING.md)。完整说明见 [docs/项目文档.md](docs/项目文档.md)。

## 生产部署

```bash
cd frontend && npm run build
python manage.py collectstatic --noinput
gunicorn django_proxy.asgi:application -c gunicorn.conf.py
```

- `DJANGO_DEBUG=false`、强 `SECRET_KEY`
- Channels 多进程时配置 `REDIS_URL`
- **限制 `/api/` 访问**（防火墙 / 内网 / 反向代理鉴权），管理 API 默认无登录

## 注意事项

1. httpx 使用 `trust_env=False`，避免系统代理把请求绕回本网关。
2. 上游 Django 需在 `ALLOWED_HOSTS` 中允许代理发出的 `Host`。
3. HTTPS 用 IP 访问上游时可能证书不匹配，见文档 `PROXY_SSL_VERIFY`。
4. 代理不自动跟跳重定向，`Location` 会改写为网关地址。

## 许可证

按项目需要自行补充。
