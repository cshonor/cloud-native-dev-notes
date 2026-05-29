# Docker 命令速查

## 镜像

```bash
docker pull <image>[:tag]
docker images
docker rmi <image>
docker build -t <name>:<tag> .
docker tag <src> <dest>
docker push <image>
```

## 容器

```bash
docker run -d --name <name> -p <host>:<container> <image>
docker ps [-a]
docker stop|start|restart <container>
docker rm <container>
docker exec -it <container> /bin/sh
docker logs [-f] <container>
```

## 网络 & 卷

```bash
docker network ls|create|rm
docker volume ls|create|rm
docker run -v <vol>:<path> ...
```

## Compose

```bash
docker compose up -d
docker compose down
docker compose ps
docker compose logs -f
```

## 清理

```bash
docker system prune -a
docker volume prune
```
