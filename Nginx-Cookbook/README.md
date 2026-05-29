# NGINX Cookbook

《NGINX Cookbook》（Derek DeJonghe，O'Reilly）学习笔记。本书为**食谱式结构**（按场景查配方），学习时按下方模块优先级跳读对应章节即可。

> **后端定位**：反向代理、路由转发、HTTPS、限流、日志排错；能看懂 K8s Ingress 配置逻辑。  
> **不做**：源码编译、自定义模块、内核调优、Nginx 集群运维。

---

## 学习模块对照表（按后端场景）

### 🔴 必学 — 日常开发 90% 场景

| 你的学习目标 | 对应原书章节 | 核心配方 |
|--------------|-------------|----------|
| 配置结构、启停、语法校验 | **Ch 01 Basics** | `nginx.conf` 层级、`nginx -t`、reload |
| 虚拟主机、多域名 | **Ch 01 Basics** | `server_name`、多 `server` 块 |
| 反向代理 ⭐⭐⭐ | **Ch 01 Basics**、**Ch 03 Traffic Management** | `proxy_pass`、请求头透传、超时 |
| Location 路由匹配 | **Ch 03 Traffic Management** | 前缀/精确/正则、优先级 |
| 静态资源 & 动静分离 | **Ch 01 Basics** | `root`/`alias`、`try_files` |
| HTTPS / SSL | **Ch 07 Security Controls** | 证书、443、HTTP→HTTPS 跳转 |
| 访问日志 & 排错 | **Ch 14 Debugging and Troubleshooting** | access/error log、看懂 404/502/503 |
| 限流 & IP 访问控制 | **Ch 07 Security Controls** | `limit_req`、`allow`/`deny` |

### 🟡 选学 — 用到再查

| 学习目标 | 对应原书章节 | 说明 |
|----------|-------------|------|
| upstream 负载均衡 | **Ch 02 Load Balancing** | 轮询、权重；生产大规模交给 K8s Service/Ingress |
| URL 重写 | **Ch 03 Traffic Management** | 简单 `rewrite`；复杂正则不深究 |
| 缓存 | **Ch 04 Content Caching** | 了解概念即可 |
| Gzip 压缩 | **Ch 01 Basics** / **Ch 15** 片段 | 按需开启 |
| Docker 跑 Nginx | **Ch 11 Containers/Microservices** | 官方镜像、挂载配置 |

### ⚫ 跳过 — 运维/架构范畴

| 内容 | 对应原书章节 |
|------|-------------|
| 源码编译、Lua/OpenResty、njs 高阶 | Ch 05 Programmability |
| JWT/OIDC/WAF/ModSecurity | Ch 06 Authentication、Ch 07 高级安全 |
| HTTP/2 深度调优 | Ch 08 HTTP/2 |
| 媒体流 | Ch 09 Media Streaming |
| 云上部署 Nginx Plus | Ch 10 Cloud Deployments |
| Nginx HA 集群 | Ch 12 HA Deployment |
| 监控大盘、Plus API | Ch 13 Monitoring、Ch 16 Controller |
| 内核/连接数极限调优 | Ch 15 Performance Tuning |

---

## 章节对照表（原书 17 章）

| 章 | 原书目录 | 优先级 |
|----|----------|--------|
| 01 | Basics | ✅ **必学** ⭐ |
| 02 | High-Performance Load Balancing | 🔄 选学 |
| 03 | Traffic Management | ✅ **必学** ⭐ |
| 04 | Massively Scalable Content Caching | 🔄 选学 |
| 05 | Programmability and Automation | ❌ 跳过 |
| 06 | Authentication | ❌ 跳过 |
| 07 | Security Controls | ✅ **必学**（HTTPS、限流、IP 控制） |
| 08 | HTTP/2 | 🔄 选学 |
| 09 | Sophisticated Media Streaming | ❌ 跳过 |
| 10 | Cloud Deployments | ❌ 跳过 |
| 11 | Containers/Microservices | 🔄 选学 |
| 12 | High-Availability Deployment Modes | ❌ 跳过 |
| 13 | Advanced Activity Monitoring | ❌ 跳过 |
| 14 | Debugging and Troubleshooting | ✅ **必学** |
| 15 | Performance Tuning | ❌ 跳过 |
| 16 | Introduction to NGINX Controller | ❌ 跳过 |
| 17 | Practical Ops Tips and Conclusion | 🔄 选学 |

---

## 必做实操清单

- [ ] 写一份反向代理配置，转发到本地 Spring Boot / Go 后端
- [ ] 配置 HTTPS + HTTP 强制跳转
- [ ] 配置 IP 黑白名单 + 基础 `limit_req` 限流
- [ ] 故意制造 502，通过 error log 定位原因
- [ ] 对照 K8s Ingress YAML，能说出每条 annotation 对应的 Nginx 行为

---

## 配置模板（`supplement/`）

| 文件 | 用途 |
|------|------|
| `reverse-proxy.conf` | 反向代理 + 请求头透传 |
| `static-and-proxy.conf` | 动静分离 |
| `https-redirect.conf` | SSL + HTTP 跳转 |
| `rate-limit-access.conf` | 限流 + IP 控制 |

---

## 学完后端能力自检

- [ ] 能手写反向代理、路由、HTTPS 配置
- [ ] 能通过日志排查 502/503/404
- [ ] 会做简单限流和 IP 访问控制
- [ ] 看懂 Nginx Ingress 路由规则，能对应调整

---

## 学习进度

| 章节文件夹 | 状态 |
|------------|------|
| chapter-01-basics | ⬜ 未开始 |
| chapter-02-load-balancing | ✅ 已完成（选学） |
| chapter-03-traffic-management | ✅ 已完成 |
| chapter-04-caching | ⬜ 未开始 |
| chapter-05-programmability | ⏭️ 跳过 |
| chapter-06-authentication | ⏭️ 跳过 |
| chapter-07-security-controls | ⬜ 未开始 |
| chapter-08-http2 | ⬜ 未开始 |
| chapter-09-media-streaming | ⏭️ 跳过 |
| chapter-10-cloud-deployments | ⏭️ 跳过 |
| chapter-11-containers | ⬜ 未开始 |
| chapter-12-ha-deployment | ⏭️ 跳过 |
| chapter-13-monitoring | ⏭️ 跳过 |
| chapter-14-debugging-logs | ⬜ 未开始 |
| chapter-15-performance-tuning | ⏭️ 跳过 |
| chapter-16-nginx-controller | ⏭️ 跳过 |
| chapter-17-practical-ops | ⬜ 未开始 |

> 状态：⬜ 未开始 / 🔄 进行中 / ✅ 已完成 / ⏭️ 跳过
