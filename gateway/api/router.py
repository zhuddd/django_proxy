from ninja import NinjaAPI

from gateway.api import auth, config, logs, nodes, routes
from gateway.api.auth_jwt import JWTAuth

api = NinjaAPI(
    title="Transparent Proxy Gateway",
    version="1.0.0",
    urls_namespace="gateway-api",
    auth=JWTAuth(),
)

api.add_router("/auth", auth.router, tags=["Auth"])
api.add_router("/routes", routes.router, tags=["Routes"])
api.add_router("/nodes", nodes.router, tags=["Nodes"])
api.add_router("/logs", logs.router, tags=["Logs"])
api.add_router("/config", config.router, tags=["Config"])
