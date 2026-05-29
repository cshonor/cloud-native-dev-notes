# Docker Compose V2 补漏（书中无专章）

《Docker 即学即用》**没有独立 Compose 章节**。多容器编排（PG + 应用 + 插件）必须单独学习当前主流的 **Compose V2**。

- 官方文档：[Docker Compose](https://docs.docker.com/compose/)
- 命令形式：`docker compose`（**无短横线**，Compose 作为 Docker CLI 插件）

---

## 命令对照

| 旧命令（V1 独立二进制） | 新命令（V2 插件） |
|-------------------------|-------------------|
| `docker-compose up -d` | `docker compose up -d` |
| `docker-compose down` | `docker compose down` |
| `docker-compose ps` | `docker compose ps` |
| `docker-compose logs -f` | `docker compose logs -f` |
| `docker-compose exec ...` | `docker compose exec ...` |

配置文件推荐命名 **`compose.yaml`**（也支持 `docker-compose.yml`）。

```bash
docker compose up -d --build
docker compose config          # 校验并展开配置
docker compose down -v         # 停止并删除命名卷（慎用，会删数据）
```

---

## 实操模板：PostgreSQL + pgvector

贴合 PostgreSQL / pgvector 技术栈，可直接运行：

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: pg-vector
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
      POSTGRES_DB: business_db
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pg_data:
```

> 注：Compose V2 可省略顶层 `version:` 字段；镜像 tag 以 [pgvector/pgvector](https://hub.docker.com/r/pgvector/pgvector) 当前标签为准。

### 常用命令

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f postgres

# 进入 psql
docker compose exec postgres psql -U dev business_db

# 停止容器（保留数据卷）
docker compose down

# 查看运行状态
docker compose ps
```

### 验证 pgvector 扩展

```sql
-- 在 psql 内执行
CREATE EXTENSION IF NOT EXISTS vector;
\dx
```

---

## 学习路径建议

1. **单 PG**：用上文模板跑通 `up` / `exec` / `logs` / `down`
2. **加应用服务**：同一 `compose.yaml` 增加 `api` 服务，`depends_on: [postgres]`，用服务名 `postgres` 作主机名连接
3. **换 TimescaleDB**：镜像改为 `timescale/timescaledb:latest-pg16`，验证扩展与迁移脚本
4. **持久化**：理解 **named volume**（`pg_data`）vs bind mount（`./init.sql:/docker-entrypoint-initdb.d/`）

---

## 与本书章节的衔接

| 本书章节 | Compose 中的体现 |
|----------|------------------|
| Ch 4 映像 | `image:` / `build:` |
| Ch 5 容器 | `services`、端口、`volumes`、`restart` |
| Ch 6 探索 | `docker compose logs`、`compose exec` |
| Ch 7 生产 | 环境变量注入、测试后 push 镜像（生产用 K8s 而非 Compose 扛分布式） |
| Ch 8 调试 | `compose ps`、`inspect` 单容器、网络连通性 |

---

## 生产环境提醒

- Compose 适合 **本地开发 / 单机集成测试**
- 分布式生产用 **Kubernetes**（见《K8s Up & Running》笔记）
- 勿把含明文密码的 `compose.yaml` 提交到公开仓库；生产用 `.env` + secrets
