# Self Host Server API

这是一个自托管服务器的API后端项目。

## 开发环境设置

1. 安装Python 3.13或更高版本
2. 安装项目依赖：
   ```bash
   pip install .
   ```

## 主要功能

- UPnP端口映射（使用miniupnpc）
- 阿里云DNS解析管理
- RESTful API接口

## 配置说明

### 阿里云DNS配置
需要在环境变量或配置文件中设置以下参数：
```bash
ALIYUN_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
```

## 开发指南

1. 启动开发服务器：
   ```bash
   uvicorn src.app.main:app --reload
   ```

2. API文档访问：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 项目结构

```
api/
├── src/
│   └── app/        # 应用程序代码
├── tests/          # 测试文件
├── pyproject.toml  # 项目配置
└── README.md       # 项目文档
```

## P2P 打洞

后端通过官方 `frpc` 管理 XTCP TCP 服务，可选择 STCP 自动中继回退。
先提供公网 `frps`，在 `.env` 设置 `P2P_SERVER_ADDR`、`P2P_SERVER_PORT`、
`P2P_TOKEN`、`P2P_BINARY`，并按需配置 TLS CA 与 STUN；全部变量见
[.env.example](.env.example)。在 `api/` 执行 `alembic upgrade head` 创建
`p2p_services` 表，后端启动时恢复已启用服务。

管理页面为 `/p2p`，`/api/p2p` 的读取、CRUD、协调、轮换密钥与 visitor/CA
下载接口均要求有效管理员。visitor TOML 含共享 frps token 和服务访问密钥，
需私密保存；访问者需要自行运行 `frpc`，连接本机回环端口。
配置步骤、运行命令、完整 API 路由和验证边界见 [P2P 文档](../docs/p2p.md)。
