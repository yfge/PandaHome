# Self Host Server

一个用于个人管理家庭主机的服务，提供动态 DDNS 和 UPnP 端口映射功能。

## 功能特性

### 动态 DDNS
- 自动更新阿里云 DNS 解析记录
- 支持多域名管理
- 实时同步公网 IP 地址
- 支持自定义解析记录类型

### UPnP 端口映射
- 自动向路由器注册端口映射
- 支持 TCP/UDP 协议
- 动态端口管理
- 实时状态监控

## 技术栈

### 前端
- Next.js 14
- TypeScript
- Tailwind CSS
- shadcn/ui
- next-intl (国际化)

### 后端
- FastAPI
- Python 3.8+
- 阿里云 DNS API
- UPnP 协议

## 开始使用

### 前置要求
- Node.js 18+
- Python 3.8+
- 阿里云 DNS API 凭证
- 支持 UPnP 的路由器

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/self-host-server.git
cd self-host-server
```

2. 安装后端依赖：
```bash
cd api
pip install -r requirements.txt
```

3. 安装前端依赖：
```bash
cd web
npm install
```

4. 配置环境变量：

在 `api` 目录下创建 `.env` 文件：
```env
ALIYUN_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
```

在 `web` 目录下创建 `.env.local` 文件：
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### 运行应用

1. 启动后端服务器：
```bash
cd api
uvicorn app.main:app --reload
```

2. 启动前端开发服务器：
```bash
cd web
npm run dev
```

3. 在浏览器中打开 [http://localhost:3000](http://localhost:3000)。

## 使用说明

### 动态 DDNS 配置
1. 在阿里云控制台获取 API 密钥
2. 配置环境变量中的 API 密钥
3. 在 Web 界面添加需要管理的域名
4. 系统会自动检测并更新公网 IP

### UPnP 端口映射
1. 确保路由器已开启 UPnP 功能
2. 在 Web 界面添加需要映射的端口
3. 系统会自动向路由器注册端口映射
4. 可以随时查看和管理端口映射状态

## API 文档

当后端服务器运行时，API 文档可在 [http://localhost:8000/docs](http://localhost:8000/docs) 访问。

### 主要接口

#### DDNS
- `GET /api/domains/domains` - 获取所有域名
- `GET /api/domains/domains/{domain}/records` - 获取域名解析记录
- `POST /api/domains/domains/{domain}/records` - 添加新的解析记录
- `DELETE /api/domains/records/{record_id}` - 删除解析记录

#### UPnP
- `GET /api/upnp/mappings` - 获取所有 UPnP 映射
- `POST /api/upnp/mappings` - 添加新的 UPnP 映射
- `PUT /api/upnp/mappings/{id}` - 更新 UPnP 映射
- `DELETE /api/upnp/mappings/{id}` - 删除 UPnP 映射

## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m '添加一些特性'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。 