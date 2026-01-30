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
