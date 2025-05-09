# PandaHome

一个懒人开发者的家庭服务器管理解决方案，集成了阿里云 DNS API 动态 DDNS 和 UPnP 自动端口映射功能。

## 功能特点

- **动态 DDNS**：自动使用阿里云 DNS API 更新解析记录，支持多域名、实时公网 IP 同步、自定义记录类型。
- **UPnP 端口映射**：自动向路由器注册端口映射，支持 TCP/UDP 协议，动态端口管理，实时状态监控。
- **Web 界面**：现代化响应式设计，支持中英文切换。
- **多语言支持**：可在英文和中文间自由切换。

## 技术栈

- **前端**：Next.js 14、TypeScript、Tailwind CSS、Shadcn UI、next-intl
- **后端**：FastAPI（Python 3.8+）、UPnP 库、阿里云 DNS API

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yfge/PandaHome.git
cd PandaHome
```

### 2. 安装依赖

```bash
# 后端
cd api
pip install -r requirements.txt

# 前端
cd web
npm install
```

### 3. 配置环境变量

```bash
# 后端 (.env)
ALIYUN_ACCESS_KEY_ID=你的访问密钥ID
ALIYUN_ACCESS_KEY_SECRET=你的访问密钥密码
ALIYUN_REGION_ID=cn-hangzhou

# 前端 (.env.local)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4. 运行应用

```bash
# 后端
cd api
uvicorn main:app --reload

# 前端
cd web
npm run dev
```

- Web 界面：http://localhost:3000
- API 文档：http://localhost:8000/docs

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