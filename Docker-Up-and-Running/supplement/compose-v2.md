# Compose V2 命令对照

第二版书写的是 `docker-compose`，现在统一用 **Compose V2 插件**：

| 旧命令 | 新命令 |
|--------|--------|
| `docker-compose up -d` | `docker compose up -d` |
| `docker-compose down` | `docker compose down` |
| `docker-compose ps` | `docker compose ps` |
| `docker-compose logs -f` | `docker compose logs -f` |

配置文件推荐命名 `compose.yaml`（也支持 `docker-compose.yml`）。

```bash
docker compose up -d --build
docker compose config    # 校验并展开配置
```
