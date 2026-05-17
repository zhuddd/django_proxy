# PyPI 包：`transparent-proxy-gateway`

后端网关以独立 Django App 发布，可在任意 Django 项目中通过 pip 安装复用。源码内已附**简体中文**模块与函数注释，便于二次开发。

## 安装

```bash
pip install transparent-proxy-gateway

# 可选：Channels 使用 Redis
pip install "transparent-proxy-gateway[redis]"

# 本仓库本地开发
pip install -e ".[dev,redis]"
```

## 最小集成

### 1. `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    # ...
    "daphne",   # 若使用 ASGI / Channels
    "channels",
    "transparent_proxy_gateway",
]
```

### 2. 中间件

```python
MIDDLEWARE = [
    # ...
    "transparent_proxy_gateway.middleware.proxy_gate.ProxyGateMiddleware",
]
```

`ProxyGateMiddleware` 为 `/api/`、`/ws/` 等路径打上 `request.proxy_skip`。前端路径请在宿主 settings 中设置 `PROXY_EXTRA_SKIP_PREFIXES`（如 `"/assets/"`）。

### 3. 默认配置（可选）

```python
from transparent_proxy_gateway.conf import inject_settings

inject_settings(globals())  # 不覆盖你已定义的同名项
```

主要默认值见 `transparent_proxy_gateway/conf.py`（`PROXY_*`、`HEALTH_CHECK_*` 等）。

### 4. `urls.py`

```python
from django.urls import path
from ninja import NinjaAPI
from transparent_proxy_gateway.integration import build_proxy_catchall, mount_gateway_routers

api = NinjaAPI(title="My Project", version="1.0")
mount_gateway_routers(api)  # 或手动 api.add_router("/routes", routes_router, ...)

urlpatterns = [
    path("api/", api.urls),
    build_proxy_catchall(),  # 必须放在最后
]
```

亦可分别导入 ``routes_router``、``logs_router`` 等，自定义挂载路径与标签（见 ``transparent_proxy_gateway.api``）。

管理台 UI 由宿主项目自行提供（独立站点、CDN 或自建 SPA 路由）。本仓库演示见 `django_proxy/frontend_urls.py`。

### 5. `asgi.py`（实时日志 WebSocket）

```python
from transparent_proxy_gateway.integration import get_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(get_websocket_urlpatterns()))
    ),
})
```

### 6. 数据库

网关包**不参与**数据库连接管理：在宿主项目 `settings.py` 中自行配置 `DATABASES`（与现有应用共用同一库即可）。

```python
# 宿主 settings.py 示例
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "myproject",
        # USER / PASSWORD / HOST / PORT ...
    }
}
```

```bash
# 在宿主库中创建网关表
python manage.py migrate transparent_proxy_gateway
python manage.py init_gateway
```

演示仓库的数据库解析与 SQLite WAL 见 `django_proxy/database.py`，**勿从网关包导入**。

## 管理 API 说明

- **无登录 / 无 JWT**：所有 `/api/*` 端点默认公开，生产环境请自行在网络层限制访问。
- OpenAPI：`/api/docs`

| 前缀 | 说明 |
|------|------|
| `/api/routes` | 路由 CRUD |
| `/api/nodes` | 健康状态 |
| `/api/logs` | 访问日志 |
| `/api/logs/stats/*` | 统计聚合 |
| `/api/config` | 系统 KV 配置 |

## 环境变量

与演示项目 `.env.example` 一致，常用：

| 变量 | 说明 |
|------|------|
| `PROXY_FORWARD_MODE` | `stream`（默认）或 `buffered` |
| `PROXY_SSL_VERIFY` | 上游 HTTPS 是否校验证书 |
| `PROXY_SSL_CA_BUNDLE` | 自定义 CA 路径 |
| `HEALTH_CHECK_*` | 后台健康检查 |
| `DATABASE_URL` | PostgreSQL / MySQL / SQLite 连接 |
| `DJANGO_DB_*` | 分项数据库配置（无 URL 时） |
| `REDIS_URL` | Channels 多进程时使用 |

## 包内目录

```
transparent_proxy_gateway/
├── api/              # Django-Ninja 管理接口
├── proxy/            # 流式转发、路由匹配、SSL、重定向改写
├── services/         # 健康检查、日志、统计
├── integration.py    # urls / asgi 辅助函数
├── conf.py           # 默认 settings
└── migrations/
```

## 发布到 PyPI

```bash
pip install build twine
python -m build
twine upload dist/*
```

## 与本仓库关系

| 路径 | 角色 |
|------|------|
| `transparent_proxy_gateway/` | 可发布包 |
| `django_proxy/` | 演示项目（settings / urls / asgi） |
| `frontend/` | Vue 管理台（不包含在 PyPI 包内） |

完整功能说明见 [项目文档.md](项目文档.md)。
