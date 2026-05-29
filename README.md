# Cloud Native 后端云原生学习笔记

## 📚 本仓库对应学习书籍
1. 《Docker 即学即用》(Docker Up and Running)
2. 《Kubernetes Up & Running》
3. 《Learning GitHub Actions》
4. 《NGINX Cookbook 经典实例》

## 🎯 仓库定位
本人后端开发，不求专职运维深耕，只吃透现代后端必备的云原生交付全链路：
- 应用容器化打包
- K8s 服务编排与部署
- Nginx 网关反向代理
- GitHub Actions 自动化 CI/CD

## 📂 目录说明
- 每个顶层文件夹 = 对应一本书
- 每本书内按原书章节拆分学习笔记、实操代码、踩坑记录

## 📖 学习顺序（形成完整交付链路）

```
Docker 打包镜像
    ↓
Kubernetes 部署与调试
    ↓
Nginx 反向代理 / Ingress 路由
    ↓
GitHub Actions 串联：代码 → 镜像 → K8s 自动发布
```

1. **Docker Up and Running** — 会写 Dockerfile、Compose，能推镜像
2. **Kubernetes Up and Running** — 会写 YAML、Deployment/Service、kubectl 调试
3. **NGINX Cookbook** — 反向代理、HTTPS、限流；理解 Ingress 底层逻辑
4. **Learning GitHub Actions** — 测试 → 构建镜像 → 推送 → `kubectl` 更新 K8s
