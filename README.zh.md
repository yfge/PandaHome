# PandaHome

一个懒人开发者的家庭服务器管理解决方案，集成了阿里云 DNS API 动态 DDNS 和 UPnP 自动端口映射功能。

## 功能特点

### 公网服务自动维护

管理员进入 **公网服务**（`/access`），填写已有服务的内网地址与端口即可保存。
自动模式检测公网 IPv4、上级 NAT、CGNAT 或证据不足，并维护直连 UPnP + 可选
阿里云 DDNS，或使用成熟的 frp 公网中转。配置持久保存；关闭页面后仍会继续
续期映射、同步变化的 IP、重试失败检查，并恢复异常退出的中转客户端。

启动前按下方“快速开始”准备数据库。使用中转时，安装官方 `frpc`，
在 **公网服务 → 连接设置与帮助**（`/access/setup`）保存已准备好的公网 `frps`、
TLS 信任信息及可选的 SSH 控制通道。管理员配置保存在部署私有文件中，
`RELAY_*` 环境变量继续作为默认值。
每套数据库和状态目录只运行一个 API worker；系统不会代为购买或部署公网服务器。

现有 GPUFree Git 入口已由 PandaHome 接管，SSH 与 frpc 均随应用管理，
原 DNS 记录及云端 frps 保持不变；进度见
[集成任务](tasks.md#relay-integration-and-retained-service-takeover-2026-10-29)，
接管与回退要求见[公网访问指南](docs/public-access.md#relay-profile-and-ssh-integration)。
该保留入口的 TCP 8081 现已启用家庭网络 SSH 自动验证；
[验收记录](docs/public-access.md#retained-automatic-tcp-verification-2026-10-29)
区分探针设施故障与业务中断。

只有映射或中转注册成功、外网检查尚未通过时，会显示 **待外网验证**。可通过 `ACCESS_PROBE_URL` 接入位于
外部网络的 HTTPS Prometheus blackbox exporter，完成 TCP 公网探测；也可显式设置
`ACCESS_PROBE_PROVIDER=ssh` 和私有 `ACCESS_PROBE_SSH_CONFIG_FILE`，通过已信任的
外部 SSH 主机执行有界 TCP 连接，无需在远端安装服务。两种方式均只证明 TCP 可达；可选
`ACCESS_ALERT_WEBHOOK` 在持续失败或已验证恢复时通知。UDP 需要从外网按业务协议验证。
详细步骤、变量与故障处理见[公网访问指南](docs/public-access.md)。

- **动态 DDNS**：自动使用阿里云 DNS API 更新解析记录，支持多域名、实时公网 IP 同步、自定义记录类型。
- **UPnP 端口映射**：自动向路由器注册端口映射，支持 TCP/UDP 协议，动态端口管理，实时状态监控。管理员可[选择上游路由器并逐层配置 NAT 映射](docs/upnp-multiple-routers.md)，新增 `/api/upnp/gateways` 及其检查、映射接口。
- **Web 界面**：现代化响应式设计，支持中英文切换。
- **多语言支持**：可在英文和中文间自由切换。

## 技术栈

- **前端**：Next.js 16（App Router）、TypeScript、Tailwind CSS 4、shadcn/ui、next-intl
- **后端**：FastAPI（Python 3.12+）、SQLAlchemy、miniupnpc、阿里云 DNS SDK

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yfge/PandaHome.git
cd PandaHome
```

### 2. 安装依赖

使用 Python 3.12+ 和 Node.js 22.x，在仓库根目录执行：

```bash
# 后端，包含必需测试钩子使用的依赖
python3 -m venv venv
source venv/bin/activate
python -m pip install -e "api[test]"

# 前端
npm install --prefix web
```

若使用 uv，可在已激活的虚拟环境中将 pip 安装命令替换为 `uv pip install -e "api[test]"`。
若 macOS 原生依赖编译失败，参考已验证的 [SDK 兼容说明](docs/backend-dependency-audit.md#macos-native-build-note)。

### 3. 配置环境变量

```bash
cp api/.env.example api/.env
cp web/.env.local.example web/.env.local
```

随后根据需求修改变量值（参见[环境变量](#环境变量)）。

### 4. 安装开发工具

```bash
# 在仓库根目录
python -m pip install pre-commit
pre-commit install --install-hooks
```

### 5. 准备数据库

默认 `DATABASE_URL=sqlite:///./app.db` 相对于进程当前工作目录解析。
迁移、管理员初始化和 API 启动必须在同一个 `api/` 目录执行，确保使用
同一份 `api/app.db`；以下步骤不会移动或合并其他目录中已有的数据库。
此终端继续保持后端虚拟环境激活。

```bash
# 从仓库根目录进入
cd api
alembic upgrade head
bootstrap-admin --username admin --password 'replace-with-your-password' --email admin@example.com
```

### 6. 运行应用

在上一步的同一个后端终端执行，此时仍位于 `api/`：

```bash
# 后端（监听 8003 端口以匹配前端默认配置）
uvicorn src.app.main:app --port 8003
```

开发时可按需添加 `--reload`。另开一个终端，进入仓库根目录后启动前端：

```bash
npm run dev --prefix web
```

- Web 界面：http://localhost:3000
- API 文档：http://localhost:8003/docs

## 开发流程

- 每次由智能体或双人编程产生代码改动时，必须在 `agent_chats/YYYYMMDD-HHMMSS-topic.md` 中记录，模板见 `agent_chats/README.md`。
- 在提交 PR 前，从仓库根目录运行测试，保持后端虚拟环境激活：
  - `python -m pytest -q api/tests`
  - `npm run test --prefix web`
- 在提交 PR 前运行 `pre-commit run --all-files`；钩子执行后端 Ruff 检查与修复、后端测试，以及已安装依赖时的前端 ESLint 和测试。
- 完整的工程手册请参考仓库根目录下的 `AGENTS.md`。

## 环境变量

后端（`api/.env`）

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy 数据库连接字符串；相对 SQLite 路径按进程当前工作目录解析 | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT 签名密钥，生产环境需替换 | `change-me` |
| `JWT_ALGORITHM` | JWT 签名算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | `30` |
| `AUTH_TOKEN_URL` | OAuth2 token 接口路径 | `/api/auth/token` |
| `AUTH_HASHING_SCHEMES` | Passlib 哈希算法的 JSON 数组 | `["bcrypt"]` |
| `AUTH_HASHING_DEPRECATED` | Passlib 过期哈希策略 | `auto` |
| `ALIYUN_ACCESS_KEY_ID` | 阿里云 Access Key ID，仅管理阿里云 DNS 时必填 | _(未设置)_ |
| `ALIYUN_ACCESS_KEY_SECRET` | 阿里云 Access Key Secret，仅管理阿里云 DNS 时必填 | _(未设置)_ |
| `ALIYUN_REGION_ID` | 阿里云 DNS API 区域 | `cn-hangzhou` |

前端（`web/.env.local`）

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI 后端的基础地址 | `http://localhost:8003` |

## 认证流程概述

1. 保持后端虚拟环境激活，在 `api/` 执行 `bootstrap-admin --username admin --password 'replace-with-your-password' --email admin@example.com` 初始化管理员账号（重复执行可更新密码）。
2. 启动后端和前端，访问 `http://localhost:3000/login` 并登录。
3. 登录成功后会在本地保存 token，受保护的页面（`/access`、`/p2p`、`/status`、`/upnp`、`/domains`）需要该 token 才能访问。
4. 当 token 失效或被撤销时，前端会自动退出并跳转回登录页。

更完整的认证生命周期说明请参考 `docs/auth-lifecycle.md`（环境变量、CLI 初始化、登录/退出流程等）。

## API 接口

### 状态
- `GET /api/status` - 获取系统状态快照
- `GET /health` - 健康检查

数据来源、刷新频率与故障排查请参考 `docs/monitoring.md`。

### UPnP
- `GET /api/upnp/mappings` - 获取所有端口映射
- `POST /api/upnp/mappings` - 添加新的端口映射
- `DELETE /api/upnp/mappings/{external_port}?protocol=TCP|UDP` - 删除端口映射（默认 `TCP`）

更多路由器前置条件、故障排查与安全注意事项请参考 `docs/upnp.md`。

### 域名管理
- `GET /api/domains/domains` - 获取所有域名
- `GET /api/domains/domains/{domain}/records` - 获取域名解析记录
- `POST /api/domains/domains/{domain}/records` - 添加新记录
- `PUT /api/domains/domains/{domain}/records/{record_id}` - 更新记录
- `DELETE /api/domains/domains/{domain}/records/{record_id}` - 删除记录

阿里云 DNS 的 AccessKey 配置、最小权限与限流排查请参考 `docs/domains.md`。

### P2P 打洞访问

管理员可在 `/p2p` 管理 TCP 服务，通过官方 frp XTCP 尝试打洞，并按服务选择
是否在失败时自动回退到 STCP 中继。需要可达的公网 `frps`，以及家庭侧和访问侧
的 `frpc`。在 `api/.env` 配置独立的 `P2P_*` 变量，在 `api/` 执行
`alembic upgrade head`，然后在页面下载 visitor 配置。访问者运行客户端后，
通过本机 `127.0.0.1` 端口连接；家庭侧进程运行并不代表已经打洞成功。

`/api/p2p` 下的服务管理、立即协调、密钥轮换和 visitor 配置下载接口均要求
有效管理员身份，下载的 TOML 含访问凭据。服务端与客户端运行命令、TLS 信任、
防火墙条件及结果判断见 [P2P 配置与 API 说明](docs/p2p.md)。

## 许可证

MIT
