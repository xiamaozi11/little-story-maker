# Docker 部署指南

本项目支持使用 Docker 和 Docker Compose 进行部署，方便快捷且环境隔离。

## 镜像大小估算

根据不同的基础镜像，最终镜像大小如下：

| Dockerfile | 基础镜像大小 | 预估最终大小 | 说明 |
|-----------|-------------|-------------|------|
| `Dockerfile` (slim) | ~130 MB | **250-300 MB** | 推荐，兼容性好 |
| `Dockerfile.alpine` | ~50 MB | **150-200 MB** | 最小体积，生产环境推荐 |

**镜像大小构成：**
- 基础 Python 镜像：130 MB (slim) / 50 MB (alpine)
- 系统字体和依赖：30-50 MB
- Python 包（Streamlit, ReportLab 等）：80-100 MB
- 应用代码：< 5 MB
- 其他系统文件：10-20 MB

## 快速开始

### 方法 1：使用 Docker Compose（推荐）

1. **确保已安装 Docker 和 Docker Compose**

2. **配置环境变量**

   编辑 `.env` 文件：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API Key
   ```

3. **启动服务**

   ```bash
   docker-compose up -d
   ```

4. **访问应用**

   打开浏览器访问：http://localhost:8501

5. **查看日志**

   ```bash
   docker-compose logs -f
   ```

6. **停止服务**

   ```bash
   docker-compose down
   ```

### 方法 2：使用 Docker 命令

1. **构建镜像**

   使用 slim 版本（推荐）：
   ```bash
   docker build -t storycraft:latest .
   ```

   或使用 alpine 版本（更小）：
   ```bash
   docker build -f Dockerfile.alpine -t storycraft:alpine .
   ```

2. **运行容器**

   ```bash
   docker run -d \
     --name storycraft \
     -p 8501:8501 \
     -v $(pwd)/output:/app/output \
     -e API_KEY=your-api-key-here \
     -e ARK_API_KEY=your-ark-key-here \
     -e IMAGE_SERVICE=doubao \
     storycraft:latest
   ```

3. **查看日志**

   ```bash
   docker logs -f storycraft
   ```

4. **停止容器**

   ```bash
   docker stop storycraft
   docker rm storycraft
   ```

## 环境变量配置

必需的环境变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `API_KEY` | 通义千问 API Key | `sk-xxx` |
| `ARK_API_KEY` | 豆包 API Key | `ark-xxx` |

可选的环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `IMAGE_SERVICE` | 图片服务（doubao/tongyi） | `doubao` |
| `DEFAULT_SCENES` | 默认场景数 | `10` |
| `PDF_IMAGE_QUALITY` | PDF 图片质量 | `85` |

## 数据持久化

Docker 容器默认会在 `/app/output` 目录生成文件。建议挂载本地目录以持久化数据：

```yaml
volumes:
  - ./output:/app/output
```

## 健康检查

容器包含健康检查功能，会定期检查应用状态：

```bash
docker ps
# 查看 HEALTHY 状态
```

## 性能优化

### 1. 使用 Alpine 版本

Alpine 版本镜像更小，启动更快：

```bash
docker build -f Dockerfile.alpine -t storycraft:alpine .
```

### 2. 多阶段构建（可选）

如果需要进一步优化，可以考虑多阶段构建，减少最终镜像大小。

### 3. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  storycraft:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 生产部署建议

### 1. 使用 Docker Compose

在生产环境中，建议使用 Docker Compose 并配置以下选项：

- 重启策略：`restart: always`
- 资源限制
- 日志轮转
- 健康检查

### 2. 反向代理

使用 Nginx 或 Traefik 作为反向代理：

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - storycraft
```

### 3. 安全建议

- 不要在镜像中包含 `.env` 文件
- 使用 Docker secrets 管理敏感信息
- 定期更新基础镜像
- 限制容器权限

## 故障排除

### 容器无法启动

1. 检查日志：
   ```bash
   docker logs storycraft
   ```

2. 验证环境变量：
   ```bash
   docker exec storycraft env | grep API
   ```

3. 检查端口占用：
   ```bash
   netstat -tuln | grep 8501
   ```

### 中文显示问题

如果中文无法正常显示，检查字体是否正确安装：

```bash
docker exec storycraft fc-list | grep -i noto
```

### 镜像构建失败

1. 清理缓存重新构建：
   ```bash
   docker build --no-cache -t storycraft:latest .
   ```

2. 检查网络连接，确保可以访问 PyPI

## 更新部署

1. **停止并删除旧容器**
   ```bash
   docker-compose down
   ```

2. **拉取最新代码**
   ```bash
   git pull
   ```

3. **重新构建镜像**
   ```bash
   docker-compose build
   ```

4. **启动新容器**
   ```bash
   docker-compose up -d
   ```

## Docker Hub 镜像

如果未来发布到 Docker Hub：

```bash
docker pull cnvhql/storycraft:latest
docker run -d -p 8501:8501 cnvhql/storycraft:latest
```
