# Transparent Proxy Gateway

基于 **Django + Django-Ninja + ASGI + Vue3** 的透明 HTTP 反向代理网关：动态注册路由、流式转发、可视化管理，行为类似 nginx 的**前缀转发**（非 path rewrite）。

## 特性

- 前缀转发：`/account` → `http://upstream:8000`，访问 `/account/login` 转发为 `http://upstream:8000/account/login`
- 最长前缀匹配（`/api/admin` 优先于 `/api`）
- 全异步：`httpx.AsyncClient` + `StreamingHttpResponse`，支持大文件与 chunked
- 完整透传 Headers / Cookies / Body / Query（过滤 Hop-by-Hop 头）
- 管理台：路由、节点健康、请求日志、WebSocket 实时日志、系统配置
- 日志：loguru（接管 Django logging，`print` 重定向）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 6、Django-Ninja、Daphne、httpx、Channels、SQLite、WhiteNoise、loguru |
| 前端 | Vue 3、Vite、Pinia、Element Plus |
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

# ASGI 开发服务
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

**示例路由：** 前缀 `/test` → 上游 `http://127.0.0.1:8888`  
访问 `http://127.0.0.1:8000/test/page` → 转发 `http://127.0.0.1:8888/test/page`

## 配置

复制环境变量模板并按需修改：

```bash
cp .env.example .env
```

常用项：

```env
DJANGO_SECRET_KEY=change-me
LOG_LEVEL=INFO
PROXY_FORWARD_MODE=stream    # stream | buffered（排障用）
HEALTH_CHECK_INTERVAL=30
REDIS_URL=                   # 多进程 Channels 时配置
```

## 架构概览

```
浏览器 → Daphne (ASGI)
           ├─ /api/*     → Django-Ninja（管理 API）
           ├─ /login …   → Vue SPA
           └─ /{prefix}  → proxy_view → httpx 流式转发 → 上游
```

详细架构、数据模型、扩展点见 **[docs/项目文档.md](docs/项目文档.md)**（含开发中问题与解决方案）。

## 项目结构

```
django_proxy/          # Django 项目配置、loguru
gateway/               # 代理核心、API、健康检查、WebSocket
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

1. **httpx 直连上游**：已设置 `trust_env=False`，避免系统 `HTTP_PROXY` 把请求绕回本网关导致 502。
2. **上游 Django**：`ALLOWED_HOSTS` 需包含代理发出的 `Host`（如 `127.0.0.1:8888`）。
3. **代理模式**：默认 `stream` 流式；异常排查可临时设 `PROXY_FORWARD_MODE=buffered`。

## 许可证

按项目实际需要自行补充。
