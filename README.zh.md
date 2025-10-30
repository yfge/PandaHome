# PandaHome

一个懒人开发者的家庭服务器管理解决方案，集成了阿里云 DNS API 动态 DDNS 和 UPnP 自动端口映射功能。

## 功能特点

- **动态 DDNS**：自动使用阿里云 DNS API 更新解析记录，支持多域名、实时公网 IP 同步、自定义记录类型。
- **UPnP 端口映射**：自动向路由器注册端口映射，支持 TCP/UDP 协议，动态端口管理，实时状态监控。
- **Web 界面**：现代化响应式设计，支持中英文切换。
- **多语言支持**：可在英文和中文间自由切换。

## 技术栈

- **前端**：Next.js 15（App Router）、TypeScript、Tailwind CSS 4、shadcn/ui、next-intl
- **后端**：FastAPI（Python 3.12+）、SQLAlchemy、miniupnpc、阿里云 DNS SDK

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yfge/PandaHome.git
cd PandaHome
```

### 2. 安装依赖

```bash
# 后端（在仓库根目录执行）
uv pip install --system -e api
# 或者
pip install -e api

# 前端
npm install --prefix web
```

### 3. 配置环境变量

```bash
cp api/.env.example api/.env
cp web/.env.local.example web/.env.local
```

随后根据需求修改变量值（参见[环境变量](#环境变量)）。

### 4. 安装开发工具

```bash
# 在仓库根目录
pip install pre-commit
pre-commit install --install-hooks
```

### 5. 准备数据库

```bash
cd api
alembic upgrade head
bootstrap-admin --username admin --password changeme --email admin@example.com
```

### 6. 运行应用

```bash
# 后端（监听 8003 端口以匹配前端默认配置）
uvicorn src.app.main:app --reload --app-dir api/src --port 8003

# 前端
npm run dev --prefix web
```

- Web 界面：http://localhost:3000
- API 文档：http://localhost:8003/docs

## 开发流程

- 每次由智能体或双人编程产生代码改动时，必须在 `agent_chats/YYYYMMDD-HHMMSS-topic.md` 中记录，模板见 `agent_chats/README.md`。
- 在提交 PR 前运行 `pre-commit run --all-files`，钩子会自动执行 Ruff 检查/格式化（`api/`）以及安装了依赖后的 `npm run lint`（前端）。
- 完整的工程手册请参考仓库根目录下的 `agents.md`。

## 环境变量

后端（`api/.env`）

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy 数据库连接字符串 | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT 签名密钥，生产环境需替换 | `change-me` |
| `JWT_ALGORITHM` | JWT 签名算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | `30` |
| `AUTH_TOKEN_URL` | OAuth2 token 接口路径 | `/api/auth/token` |
| `AUTH_HASHING_SCHEMES` | Passlib 哈希算法（逗号分隔） | `bcrypt` |
| `AUTH_HASHING_DEPRECATED` | Passlib 过期哈希策略 | `auto` |
| `ALIYUN_ACCESS_KEY_ID` | 阿里云 Access Key ID | _(必填)_ |
| `ALIYUN_ACCESS_KEY_SECRET` | 阿里云 Access Key Secret | _(必填)_ |
| `ALIYUN_REGION_ID` | 阿里云 DNS API 区域 | `cn-hangzhou` |

前端（`web/.env.local`）

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI 后端的基础地址 | `http://localhost:8003` |

## 认证流程概述

1. 通过 `bootstrap-admin --username admin --password changeme --email admin@example.com` 初始化管理员账号（重复执行可更新密码）。
2. 启动后端和前端，访问 `http://localhost:3000/login` 并登录。
3. 登录成功后会在本地保存 token，受保护的页面（`/status`、`/upnp`、`/domains`）需要该 token 才能访问。
4. 当 token 失效或被撤销时，前端会自动退出并跳转回登录页。

## API 接口

### UPnP
- `GET /api/upnp/mappings` - 获取所有端口映射
- `POST /api/upnp/mappings` - 添加新的端口映射
- `DELETE /api/upnp/mappings/{id}` - 删除端口映射

### 域名管理
- `GET /api/domains/domains` - 获取所有域名
- `POST /api/domains/domains` - 添加新域名
- `GET /api/domains/domains/{domain}/records` - 获取域名解析记录
- `POST /api/domains/domains/{domain}/records` - 添加新记录
- `PUT /api/domains/domains/{domain}/records/{record_id}` - 更新记录
- `DELETE /api/domains/domains/{domain}/records/{record_id}` - 删除记录

## 许可证

MIT
