# buildx 多架构构建

> 补充多平台镜像构建（arm64 / amd64）。

## 创建 builder

```bash
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap
```

## 构建并推送多架构镜像

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myregistry/myapp:latest \
  --push .
```

## 本地加载单架构（调试用）

```bash
docker buildx build --platform linux/amd64 -t myapp:local --load .
```

## 查看支持的平台

```bash
docker buildx ls
```

## 注意事项

- `--load` 仅支持单平台，多平台必须 `--push` 到 registry
- CI 中常用 `QEMU` 模拟非本机架构：`docker run --privileged --rm tonistiigi/binfmt --install all`
