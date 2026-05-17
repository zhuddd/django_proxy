# Transparent Proxy Gateway

基于 **Django + Django-Ninja + ASGI + Vue3** 的透明 HTTP 反向代理网关：动态注册路由、流式转发、可视化管理，行为类似 nginx 的**前缀转发**（非 path rewrite）。

## 特性

- **前缀转发**：`/account` → `http://upstream:8000`，访问 `/account/login` 转发为 `http://upstream:8000/account/login`
- **通配符路由**：支持 `/*`、`/robot/*` 等；每个通配作用域仅允许一条上游
- **最长前缀匹配**：精确前缀优先于同作用域通配；`/api/admin` 优先于 `/api`
- **全异步**：`httpx.AsyncClient` + `StreamingHttpResponse`，支持大文件与 chunked
- **透传**：Headers / Cookies / Body / Query（过滤 Hop-by-Hop 头）
- **响应改写**：`Set-Cookie` Path、`Location`（301/302/303/307/308）、`Referer`/`Origin` 适配网关前缀
- **管理台**：路由、节点健康、请求日志、**请求统计（ECharts）**、WebSocket 实时日志、系统配置
- **HTTPS 上游**：可配置证书校验或内网跳过校验（见 `PROXY_SSL_VERIFY`）
- **日志**：loguru（接管 Django logging，`print` 重定向）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 6、Django-Ninja、Daphne、httpx、Channels、SQLite、WhiteNoise、loguru |
| 前端 | Vue 3、Vite、Pinia、Element Plus、ECharts |
| 部署 | Gunicorn + UvicornWorker |

## 快速开始

### 1. 后端

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py init_gateway
python manage.py createsuperuser

python manage.py runserver 8000
# 或: daphne -b 0.0.0.0 -p 8000 django_proxy.asgi:application
```

### 2. 前端

```bash
cd frontend
npm install
npm run build          # 产物 -> frontend/dist
# 开发: npm run dev     # http://localhost:5173，API 代理到 8000
```

### 3. 访问

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/login | 管理台登录 |
| http://127.0.0.1:8000/api/docs | Ninja API 文档 |
| http://127.0.0.1:8000/{prefix}/... | 已注册前缀的代理流量 |

**示例（精确前缀）：** `/test` → `http://127.0.0.1:8888`  
访问 `http://127.0.0.1:8000/test/page` → 转发 `http://127.0.0.1:8888/test/page`

**示例（通配符）：**

| 前缀 | 匹配 |
|------|------|
| `/robot/*` | `/robot`、`/robot/api/...` |
| `/*` | 全局兜底（全站仅可配置一条） |

## 配置

```bash
cp .env.example .env
```

常用项：

```env
DJANGO_SECRET_KEY=change-me
LOG_LEVEL=INFO

PROXY_FORWARD_MODE=stream       # stream | buffered（排障）
PROXY_SSL_VERIFY=true           # false：HTTPS 用 IP 且无匹配证书时
# PROXY_SSL_CA_BUNDLE=/path/to/ca.pem

HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_CONCURRENCY=5
REDIS_URL=                      # 多进程 Channels 时配置
```

## 架构概览

```
浏览器 → Daphne (ASGI)
           ├─ /api/*     → Django-Ninja（管理 API + JWT）
           ├─ /login …   → Vue SPA（含 /stats 统计页）
           └─ /{prefix}  → proxy_view → httpx 流式转发 → 上游
```

详细说明见 **[docs/项目文档.md](docs/项目文档.md)**（架构、API、通配符、重定向、SSL、FAQ）。

## 管理 API 摘要

| 路径 | 说明 |
|------|------|
| `POST /api/auth/login` | 登录 |
| `GET/POST /api/routes` | 路由 CRUD |
| `GET /api/nodes` | 节点健康 |
| `POST /api/nodes/check` | 立即检测 |
| `GET /api/logs` | 请求日志 |
| `GET /api/logs/stats/*` | 统计（overview、timeline、status、methods、top-paths） |
| `GET/PUT /api/config` | 系统配置 |

## 项目结构

```
django_proxy/          # Django 项目配置、loguru
gateway/               # 代理核心、API、健康检查、WebSocket
  proxy/               # core, client, router, route_rules, response_rewrite, ssl_config
frontend/              # Vue 管理台
data/                  # SQLite
logs/                  # 日志文件
docs/                  # 详细文档
```

## 生产部署

```bash
cd frontend && npm run build
python manage.py collectstatic --noinput
gunicorn django_proxy.asgi:application -c gunicorn.conf.py
```

生产环境请设置 `DJANGO_DEBUG=false`、强 `SECRET_KEY`，并为 Channels 配置 Redis。

## 注意事项

1. **httpx 直连上游**：`trust_env=False`，避免系统 `HTTP_PROXY` 绕回本网关导致 502。
2. **上游 Django**：`ALLOWED_HOSTS` 需包含代理发出的 `Host`；CSRF 依赖 Cookie/Location 改写（见文档）。
3. **HTTPS + IP**：证书通常不包含 IP SAN，请用域名作上游 URL，或设置 `PROXY_SSL_VERIFY=false`（仅可信内网）。
4. **重定向**：代理不自动跟跳（`follow_redirects=False`），301/302 等原样返回客户端，`Location` 已改写为网关地址。
5. **通配符**：`/*` 全局仅一条；`/robot/*` 与 `/robot` 下精确路由互斥（见文档）。

## 许可证

按项目实际需要自行补充。
