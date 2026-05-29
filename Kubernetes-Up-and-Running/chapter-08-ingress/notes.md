# 第八章：使用 Ingress 进行 HTTP 负载均衡 (Chapter 8: HTTP Load Balancing with Ingress)

## Ingress 简介与核心逻辑 (Introduction to Ingress)

* **核心痛点与引入背景**：
  * 之前章节中的 **Service 对象** 工作在 OSI 模型的 **第四层（Layer 4）**，仅转发 TCP 和 UDP 连接，无法解析连接内部的协议内容。
  * 如果为集群中托管的每个 HTTP 服务都分配一个独立的对外暴露的 Service（如 `NodePort` 或 `LoadBalancer`），将导致端口管理混乱，或消耗大量昂贵的云端负载均衡器资源。
* **核心定义**：
  * **Ingress** 是 Kubernetes 中用于实现 HTTP 层（第七层 / Layer 7）负载均衡的原生系统。
  * **虚拟主机模式（Virtual Hosting）**：Ingress 的设计理念类似于传统的虚拟主机，通过单一的 IP 地址和标准的 HTTP(80) / HTTPS(443) 端口接收所有流量，然后充当「交通警察（Traffic cop）」，根据 HTTP 请求的 **Host 头（域名）** 和 **URL 路径（Path）** 将流量代理到后端的不同程序。

```
外部请求 → Ingress Controller (L7) → 按 Host/Path 路由 → Service → Pod
              ↑
         单 IP :80/:443
```

> 💡 **后续拓展空间**：可在此处引入 OSI 七层网络模型的图解，深入对比基于 iptables/IPVS 的四层转发与基于反向代理（Reverse Proxy）的七层转发在性能与解析能力上的本质差异。

---

## Ingress 规范与 Ingress 控制器 (Ingress Spec Versus Ingress Controllers)

* **核心架构解耦**：
  * Ingress 在实现上与 Kubernetes 中绝大多数常规资源对象截然不同。它被拆分为 **通用资源规范（Ingress Spec）** 和 **控制器实现（Ingress Controllers）** 两个独立的部分。
  * **核心警告**：Kubernetes 自身 **并没有内置标准的 Ingress 控制器**。用户仅仅创建 Ingress 对象是毫无作用的，必须自行安装和维护一个外部的控制器实现。
* **设计因果脉络**：
  * 之所以采取这种设计，是因为业界不存在「唯一标准」的 HTTP 负载均衡器。负载均衡器涵盖了开源软件（如 NGINX, HAProxy）、专有软件、硬件设备以及各大云厂商提供的原生服务（如 AWS ELB）。
  * 这种设计使得 Ingress 成为一个高度 **可插拔（Pluggable）** 的架构。

> 💡 **后续拓展空间**：可在此补充 Kubernetes 架构演进史，解释为何 Ingress 在 CRD（自定义资源定义）机制成熟之前就被引入，以及这对其底层设计造成了哪些历史遗留影响。

---

## 安装 Contour (Installing Contour)

* **生态与选型**：
  * **Contour** 是一个由 Heptio 开发并用于生产环境的开源 Ingress 控制器，其底层基于 CNCF 的 **Envoy** 代理实现。Envoy 专为通过 API 进行动态配置而设计。
* **安装逻辑与网络配置**：
  * Contour 会在 `heptio-contour` 命名空间下创建一个 Deployment 和一个 `type: LoadBalancer` 的对外 Service。
  * **DNS 联动**：为了让 Ingress 正常工作，必须在 DNS 提供商处配置 A 记录或 CNAME 记录，将业务域名（如 `alpaca.example.com`）映射到 Contour 负载均衡器分配的外部 IP 或主机名上。本地测试时则需修改本机的 `/etc/hosts` 文件。

```bash
# 示例：将域名指向 Ingress LB 外部 IP
# alpaca.example.com  →  <EXTERNAL-IP>
```

> 💡 **后续拓展空间**：可拓展 Envoy 的 xDS API 动态发现机制原理，解释 Contour 是如何将 K8s Ingress 规则实时翻译为 Envoy 配置而无需重启代理进程的。

---

## 使用 Ingress (Using Ingress)

* **三大核心路由模式**：
  1. **最简用法（默认透传 / Simplest Usage）**：
     * 不配置任何域名或路径规则，将所有抵达 Ingress 控制器的流量盲目地转发给一个指定的上游（Upstream / Backend）服务。这等同于普通的 LoadBalancer 服务，仅作为基础打底。
  2. **基于主机名的路由（Using Hostnames）**：
     * 根据 HTTP 请求中的 `Host` 头进行分发。
     * **兜底机制**：如果请求的主机名没有匹配到任何规则，某些控制器（如 NGINX）会将其发送到 `kube-system` 命名空间下名为 **`default-http-backend`** 的特殊服务。
  3. **基于路径的路由（Using Paths）**：
     * 不仅匹配主机名，还匹配请求的 URL 路径（如将 `example.com/a/` 路由到 A 服务，`/` 路由到 B 服务）。
     * **核心规则**：当同一个主机名下存在多个路径时，遵循 **最长前缀匹配（Longest prefix matches）** 原则。
* **易错细节**：
  * 请求被代理到上游服务时，**路径默认保持不变**。这意味着上游的应用程序内部必须准备好处理挂载在该子路径（如 `/a/`）下的请求。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: alpaca-ingress
spec:
  rules:
    - host: alpaca.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: alpaca-api
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: alpaca-web
                port:
                  number: 80
```

> 💡 **后续拓展空间**：可补充 Ingress YAML 清单中 `rules`、`http`、`paths` 和 `backend` 层级嵌套格式的具体代码规范与校验规则。

---

## Ingress 进阶主题与避坑指南 (Advanced Ingress Topics and Gotchas)

* **多控制器共存（Running Multiple Ingress Controllers）**：
  * 使用注解 **`kubernetes.io/ingress.class`**（或 `spec.ingressClassName`）指定该 Ingress 对象归属哪个控制器解析。若缺失此注解，多个控制器可能会同时争抢处理该对象，导致不可预知的状态覆盖。
* **对象冲突逻辑（Multiple Ingress Objects）**：
  * 如果定义了多个存在配置冲突的 Ingress 对象，Kubernetes 层面没有统一定义其合并行为。不同控制器实现的解决策略不同，极易引发线上故障。
* **命名空间隔离打破与安全隐患（Ingress and Namespaces）**：
  * **硬性安全边界**：出于安全考虑，Ingress 对象 **只能引用与其处于同一个命名空间（Namespace）下的上游 Service**。禁止跨命名空间引用以防流量劫持。
  * **架构漏洞**：不同命名空间下的 Ingress 对象可以声明绑定 **同一个域名（Host）** 的不同子路径。控制器会在全局将其合并为单一配置。这实际打破了命名空间的隔离性，要求管理员必须在全局层面协调域名的分配。
* **路径重写（Path Rewriting）**：
  * **实现机制**：通过特定控制器的注解（如 `nginx.ingress.kubernetes.io/rewrite-target`）并结合正则表达式，可在流量转发前剥离或修改 URL 路径。
  * **极高危易错点**：许多 Web 应用（尤其是前端带静态资源或绝对路径跳转的应用）假设自身运行在根目录 `/` 下。如果使用路径重写将其挂载到子目录，极易导致应用内链接大面积失效（如加载不到 CSS/JS 文件）。建议复杂应用尽量避免使用子路径部署。
* **配置 HTTPS/TLS（Serving TLS）**：
  * 通过将 TLS 证书和私钥存储为 Kubernetes **Secret（类型通常为 `kubernetes.io/tls`）**，并在 Ingress `spec.tls` 中引用该 Secret 及关联的域名，可实现 HTTPS 卸载。
  * 推荐结合开源项目 **`cert-manager`** 及 Let's Encrypt 自动完成证书的申请、签发与轮转更新。

```yaml
metadata:
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  tls:
    - hosts:
        - alpaca.example.com
      secretName: alpaca-tls
```

> 💡 **后续拓展空间**：深入探讨 K8s 安全策略中如何通过 OPA (Open Policy Agent) 或其他准入控制器限制特定命名空间可以使用哪些域名，以弥补 Ingress 的安全漏洞。

---

## 替代的 Ingress 实现 (Alternate Ingress Implementations)

* **主流控制器矩阵**：
  * **云原生实现**：AWS ALB Ingress Controller、GCP HTTP(S) Load Balancing 等，直接将 Ingress 规则映射为云厂商底层的硬件/云端负载均衡器配置。能降低集群内部负载，但通常会带来额外计费成本。
  * **开源标杆**：**NGINX Ingress Controller**，拥有极其庞大的功能集和极度依赖 Annotation（注解）的配置系统。
  * **API 网关演化**：基于 Envoy 的 Ambassador 和 Gloo，除了基础路由，更侧重于微服务 API 网关的能力。
  * **对开发者友好**：Traefik，使用 Go 编写，自带完善的可视化监控面板。

| 控制器 | 底层 | 特点 |
|--------|------|------|
| NGINX Ingress | NGINX | 生态最大，注解丰富 |
| Contour | Envoy | 动态配置，生产可用 |
| Traefik | Go 自研 | 易用，自带 Dashboard |
| 云厂商 ALB/GLB | 云 LB | 流量在集群外，有额外费用 |

> 💡 **后续拓展空间**：可对比云原生外部负载均衡（如 AWS ALB）与集群内部软负载均衡（如 NGINX）在网络跳数（Network Hops）、源 IP 保留（Source IP Preservation）方面的差异。

---

## Ingress 的未来 (The Future of Ingress)

* **当前架构局限性**：
  * Ingress API 设计严重「欠定义（Underdefined）」。由于标准字段匮乏，大量高级功能只能通过缺乏跨实现可移植性的 Annotation（注解）来拼凑。
  * 配置容易出错且容易产生冲突（特别是跨命名空间的合并行为）。
  * 设计之初未能预见到 **Service Mesh（服务网格，如 Istio, Linkerd）** 的爆发，Ingress 与服务网格的重叠与边界亟待厘清。
* **演进方向**：
  * 各种实现正在探索新的 API 抽象。例如 Contour 引入了 `IngressRoute` 自定义资源类型，采用类似 DNS 委托的设计来解决多团队/多命名空间的配置冲突问题。

> 💡 **后续拓展空间**：重点引入 Kubernetes 社区目前正在主推的下一代流量路由标准 **Gateway API**，解析它如何通过 `GatewayClass`, `Gateway`, `HTTPRoute` 三层角色分离架构彻底取代传统 Ingress。

---

## 总结 (Summary)

* **核心主旨提炼**：
  * Ingress 在 Kubernetes 中是一个极其特殊的存在：它仅仅提供了一个声明式的数据模式（Schema），而实际的流量管控能力必须由独立安装的控制器来赋予。
  * 它是以低成本和高灵活性将 HTTP/HTTPS 服务暴露给外部用户的最核心基础设施，也是连接外部物理网络与 Kubernetes 动态微服务世界的一道关键阀门。随着集群规模扩大，精通 Ingress 及其控制器的底层行为，是运维生产级 K8s 集群的必修课。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Ingress | L7 路由：单入口按 Host/Path 分发 HTTP(S) |
| Spec vs Controller | K8s 只定义规范，必须单独安装控制器 |
| 路由规则 | Host 匹配域名；Path 最长前缀优先 |
| 路径默认 | 转发到后端时 URL 路径不变 |
| ingress.class | 多控制器时指定由谁处理 |
| 命名空间 | 只能引用同 ns 的 Service；跨 ns 可拼同一 Host |
| rewrite-target | 子路径部署易坏链，前端应用慎用 |
| TLS | Secret + `spec.tls`；配合 cert-manager |
| 演进 | Ingress 欠定义 → Gateway API 是下一代 |
