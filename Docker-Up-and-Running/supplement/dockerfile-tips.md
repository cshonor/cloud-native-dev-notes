# Dockerfile 后端必备技巧

## 多阶段构建

减小最终镜像体积，只把编译产物打进运行镜像：

```dockerfile
# 构建阶段
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o server .

# 运行阶段
FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]
```

## .dockerignore

与 `.gitignore` 类似，排除不需要打进镜像的文件，加快 build、减小上下文：

```
.git
node_modules
*.md
.env
dist
```

放在 Dockerfile 同级目录，Docker 构建时自动读取。
