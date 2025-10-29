from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, domains, upnp, users
from .models.response import Response
from .services.upnp import UPNPService
from .database.database import engine
from .models.db_models import Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Self Host Server API",
    description="自托管服务器API",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建服务实例
upnp_service = UPNPService()
# 注册路由
app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(upnp.router)
app.include_router(users.router)

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化UPnP服务"""
    await upnp_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理UPnP服务"""
    await upnp_service.close()

@app.get("/health")
async def health():
    """健康检查"""
    return Response.success(data={"message": "OK"})
