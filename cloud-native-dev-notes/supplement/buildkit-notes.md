# BuildKit 笔记

> 补充《Docker 即学即用》第二版未覆盖的 BuildKit 内容。

## 启用

```bash
# Docker Desktop 默认已启用
export DOCKER_BUILDKIT=1
docker build .
```

## 优势

- 并行构建层，缓存更高效
- 支持 `--secret`、`--ssh` 安全传递凭据
- 多阶段构建性能更好

## Dockerfile 语法扩展

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=cache,target=/go/pkg/mod go build .
RUN --mount=type=secret,id=mysecret cat /run/secrets/mysecret
```

## 常用命令

```bash
docker buildx build --progress=plain .
docker buildx du    # 查看构建缓存占用
```
