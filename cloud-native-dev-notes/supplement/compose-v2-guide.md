# Docker Compose V2 指南

> 补充 Compose V2 与旧版 `docker-compose` 的差异。

## 命令变化

| 旧版 | V2 |
|------|-----|
| `docker-compose up` | `docker compose up` |
| `docker-compose down` | `docker compose down` |

Compose V2 作为 Docker CLI 插件集成，不再需要单独安装。

## compose.yaml

推荐使用 `compose.yaml`（也支持 `docker-compose.yml`）：

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    depends_on:
      - api

  api:
    build: .
    environment:
      - NODE_ENV=production
```

## 常用选项

```bash
docker compose up -d --build
docker compose watch          # 开发模式文件同步
docker compose config         # 验证并展开配置
docker compose logs -f web
```
