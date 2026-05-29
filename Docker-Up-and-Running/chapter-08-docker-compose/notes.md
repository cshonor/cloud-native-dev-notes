# 第8章 Docker Compose（第三版 · 课外必补）

> **来源说明**：你手上的 **12 章版本无 Compose 专章**；以下内容来自 **《Docker 即学即用》第三版** 结构（Ch 3 配置与启动 + Ch 8.4 命令 + Ch 8.5 配置管理），与仓库 `chapter-01`～`chapter-11` 笔记对齐。  
> **后端学习提示**：本章 **必学 ⭐⭐⭐**。本地开发标配：PG + pgvector / TimescaleDB + 后端 API 一键拉起；命令统一用 **`docker compose`**（V2，无横杠）。生产多机编排交给 K8s，Compose 仅用于本机/单机集成测试。

## Docker Compose 简介

* **核心主旨与实用要点**
  * Compose 是**多容器编排工具**，用一个 YAML 文件定义一组相关容器，实现「一次定义、一键启停」。
  * 统一处理：网络（服务名 DNS）、命名卷、环境变量、依赖顺序与健康检查。
  * 第三版默认 **Compose V2**：`docker compose`（CLI 插件）；旧版独立二进制 `docker-compose` 仅作兼容对照。
* **与单机 docker run 的因果对比**
  * *单机*：每个容器一条 `docker run`，网络/卷需手工 `--link` 或自定义网络。
  * *Compose*：声明 `services`，自动创建项目级默认网络 `<项目名>_default`，容器间用**服务名**互连（如 `postgres:5432`）。
* **后端拓展**
  * 开发环境：`compose.yml` + `.env`；勿把含密码的 `.env` 提交 Git（加入 `.gitignore`）。
  * 与 K8s：Compose `services` ≈ 简化版 Deployment + Service；`healthcheck` ≈ K8s `readinessProbe`。

```
compose.yml  →  docker compose up -d  →  网络 + 卷 + N 个容器
```

## 编写 compose.yml（配置 Docker Compose）

* **核心主旨与实用要点**
  * 默认文件名：`compose.yaml` 或 `compose.yml`（亦兼容 `docker-compose.yml`）。Compose V2 可省略顶层 `version:` 字段。
* **最简示例（PostgreSQL）**

```yaml
services:
  db:
    image: postgres:16
    container_name: mydb
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: business_db
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

* **关键字说明**
  * `services`：所有容器服务（**核心**）
  * `image`：镜像名:标签；或 `build:` 从 Dockerfile 构建
  * `container_name`：自定义容器名（可选；不填则自动生成）
  * `ports`：端口映射 `宿主机:容器`
  * `environment`：环境变量（明文）；敏感项优先放 `.env`
  * `volumes`：命名卷持久化（PG 数据目录必挂）
* **后端拓展：pgvector 镜像**

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
      POSTGRES_DB: business_db
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
```

| 关键字 | 作用 | PG 场景 |
|--------|------|---------|
| `services` | 服务列表 | db + api |
| `volumes` | 命名卷 | `/var/lib/postgresql/data` |
| `ports` | 宿主机访问 | `5432:5432` |
| `environment` | 初始化账号库名 | `POSTGRES_*` |

## 启动服务

* **核心主旨与实用要点**
  * 在 `compose.yml` 所在目录执行 `docker compose up`；`-d` 后台运行。
* **启动时自动完成**
  * 创建默认网络（如 `myproject_default`）
  * 创建声明的命名卷（如 `postgres-data`）
  * 按 `depends_on` 顺序启动容器（**注意**：默认只等「容器启动」，不等「服务就绪」——见下一节健康检查）
* **常用命令**

```bash
# 前台启动（看日志，Ctrl+C 停）
docker compose up

# 后台启动（常用）
docker compose up -d

# 启动前重新构建自定义镜像
docker compose up -d --build
```

## 健康检查（Health Check）

* **核心主旨与实用要点**
  * 第三版强调**服务就绪检查**，避免「容器已启动但 PostgreSQL 尚未 accept 连接」导致应用连库失败。
  * `healthcheck` 定期在容器内执行探测命令；状态为 `healthy` / `unhealthy` / `starting`。
* **示例：给 db 加健康检查**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```

* **配合 depends_on 等待健康（重点）**

```yaml
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    image: myapp:latest
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://user:secret@db:5432/business_db
```

* **易错细节**
  * 仅写 `depends_on: [db]`：**不保证** PG 已 ready，应用仍可能启动即崩溃。
  * `condition: service_healthy` 需 db 侧配置 `healthcheck`，否则无效。
  * 连接串主机名用**服务名** `db`，不是 `localhost`（在 app 容器网络命名空间内）。
* **后端拓展：与 K8s 对照**

| Compose | K8s |
|---------|-----|
| `healthcheck` | `livenessProbe` / `readinessProbe` |
| `depends_on` + `service_healthy` | Init Container 或 readiness 门控 |
| 服务名 DNS `db` | Service 名 `postgres.default.svc` |

```bash
docker compose ps    # 查看 HEALTH 列：healthy / unhealthy
```

## Docker Compose 命令

* **核心主旨与实用要点**
  * 第三版常用命令均为 **V2 格式** `docker compose <子命令>`；与单机 `docker` 命令互补。

### 启动 / 停止

```bash
docker compose up -d          # 后台启动所有服务
docker compose stop           # 停止服务，不删容器
docker compose down           # 停止并删除容器、网络（保留卷）
docker compose down -v        # 彻底删除卷（⚠️ PG 数据清空）
```

### 查看状态 / 日志

```bash
docker compose ps             # 列出项目内容器及健康状态
docker compose logs           # 所有服务日志
docker compose logs -f db     # 实时跟踪 db
docker compose logs --tail=100 app
```

### 进入容器 / 执行命令

```bash
docker compose exec db bash
docker compose exec db psql -U user business_db
docker compose restart db
```

### 构建 / 拉取 / 校验

```bash
docker compose build          # 构建带 build: 的服务
docker compose pull           # 拉取 image 最新层
docker compose config         # 校验 YAML 并展开变量
```

* **与单机命令对照**

| 场景 | 单机 | Compose |
|------|------|---------|
| 进容器 | `docker exec -it mydb bash` | `docker compose exec db bash` |
| 日志 | `docker logs -f mydb` | `docker compose logs -f db` |
| 列表 | `docker ps` | `docker compose ps` |

## 管理配置

* **核心主旨与实用要点**
  * Compose 支持在 YAML 中引用环境变量，配合 `.env` 实现多环境（dev/staging）配置分离，避免密码写死在仓库里。

### 默认值（缺省值）

* 语法：`${VAR:-默认值}`——变量未设置时使用默认值。

```yaml
services:
  db:
    image: postgres:${TAG:-16}    # TAG 未定义 → 用 16
```

### 强制值（必填）

* 语法：`${VAR:?提示信息}`——变量未设置则 **Compose 直接报错退出**，强制必须提供。

```yaml
services:
  db:
    environment:
      POSTGRES_PASSWORD: ${DB_PASS:?必须设置 DB_PASS}
```

### .env 文件

* **机制**：`compose.yml` **同目录**下的 `.env` 会被自动加载；也可 `--env-file` 指定其他文件。
* **.env 示例**

```
TAG=16
DB_USER=user
DB_PASS=secret
DB_PORT=5432
```

* **在 compose.yml 中引用**

```yaml
services:
  db:
    image: postgres:${TAG}
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    ports:
      - "${DB_PORT}:5432"
```

* **多环境支持**

```bash
docker compose --env-file .env.dev up -d
docker compose --env-file .env.prod up -d
```

* **易错细节与警告**
  * `.env` 中**不要加引号包裹值**（除非引号本身是值的一部分）。
  * `compose.yml` 里 `${VAR}` 与 shell 变量不同，由 Compose 解析。
  * **切勿**将 `.env` 提交公开仓库；提供 `.env.example` 作模板。

| 语法 | 含义 | 示例 |
|------|------|------|
| `${VAR}` | 直接引用 | `${DB_USER}` |
| `${VAR:-默认}` | 缺省默认值 | `${TAG:-16}` |
| `${VAR:?错误}` | 必填，否则失败 | `${DB_PASS:?设置 DB_PASS}` |

## 小结

* **核心主旨与重点结论**
  * Compose 用一份 `compose.yml` 定义多容器拓扑；V2 命令 `docker compose` 是本地 PG + 应用联调的标准工具。
  * **健康检查 + `service_healthy`** 解决「容器 up 但数据库未 ready」的经典坑。
  * **`.env` + 变量插值** 管理多环境；生产密钥用 CI/K8s Secret，不单靠 `.env` 文件上云。
* **完整开发栈示例（PG + 后端）**

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    env_file: .env
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-dev}"]
      interval: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8080:8080"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy

volumes:
  pg_data:
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Compose V2 | `docker compose`，无横杠 |
| `compose.yml` | `services` + `volumes` + 可选 `networks` |
| 服务名 DNS | app 连 `db:5432`，不是 localhost |
| `up -d` | 后台启动；自动建网络与卷 |
| `healthcheck` | `pg_isready` 探活 PG |
| `service_healthy` | 等 DB 真 ready 再启 app |
| `docker compose down` | 删容器网络，**默认保留卷** |
| `down -v` | 删卷，**数据没了** |
| `${VAR:-默认}` | 可选变量默认值 |
| `${VAR:?msg}` | 必填变量，缺则报错 |
| `.env` | 同目录自动加载；勿提交 Git |
| 生产 | Compose 仅本地/单机；集群用 K8s |
