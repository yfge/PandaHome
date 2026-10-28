import os
import time
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import access, auth, domains, status, upnp, users
from .models.response import Response
from .services.status import StatusService
from .services.upnp import UPNPService
from .services.access.controller import AccessController
from .config import settings
from .database.database import engine
from .models.db_models import Base

# 创建数据库表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skip UPnP discovery during pytest runs to keep tests fast and deterministic.
    skip_upnp = bool(os.getenv("PYTEST_CURRENT_TEST"))

    async with AsyncExitStack() as cleanup:
        if not skip_upnp:
            cleanup.push_async_callback(app.state.upnp_service.shutdown)
            cleanup.push_async_callback(app.state.access_controller.stop)
            await app.state.access_controller.start()
        yield


app = FastAPI(
    title="Self Host Server API",
    description="自托管服务器API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.started_at = time.time()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建服务实例（挂载到 app.state，方便通过 Depends 注入）
app.state.upnp_service = UPNPService()
app.state.status_service = StatusService(upnp_service=app.state.upnp_service)
app.state.access_controller = AccessController(
    app.state.upnp_service, interval=settings.ACCESS_CHECK_INTERVAL_SECONDS,
    alert_threshold=settings.ACCESS_ALERT_FAILURE_THRESHOLD,
)
# 注册路由
app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(status.router)
app.include_router(upnp.router)
app.include_router(users.router)
app.include_router(access.router)

@app.get("/health")
async def health():
    """健康检查"""
    now = time.time()
    uptime = max(0, int(now - getattr(app.state, "started_at", now)))
    return Response.success(data={"message": "OK", "timestamp": int(now), "uptime": uptime})
