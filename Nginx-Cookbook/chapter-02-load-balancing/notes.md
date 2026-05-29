# 第2章 高性能负载均衡 (High-Performance Load Balancing)

> **后端学习提示**：本章**选学**。掌握 `upstream`、轮询/最少连接/`ip_hash`、被动健康检查即可；NGINX Plus 专属能力（sticky、主动健康检查、慢启动）了解概念，生产大规模 LB 交给 K8s Service/Ingress。

## 2.0 引言 (Introduction)

* **核心主旨**：现代互联网用户体验要求极高的性能和正常运行时间，为此需要使用多副本系统并分配负载的架构技术。随着系统负载增加，必须能够横向扩展基础设施。
* **关键定义**：**水平扩展 (Horizontal scaling)** 是指运行同一系统的多个副本并对它们分配请求负载的架构技术，通常依赖于灵活的基于软件的基础设施。
* **逻辑脉络**：
  * **无状态与有状态的权衡**：现代 Web 架构倾向于无状态应用（将会话状态存储在共享内存或数据库中），但在处理庞大数据或规避网络开销时，应用可能会将状态存储在本地。对于此类应用，NGINX 提供了智能的负载均衡和会话持久化（Session Persistence）方案。
  * **容错与高可用保障**：为了防止向发生故障的后端发送请求（导致客户端超时），负载均衡器必须具备检测上游服务器可用性的能力。NGINX 开源版提供被动健康检查，而 NGINX Plus 提供主动健康检查机制。
* **预留拓展空间**：[可在此补充业务侧的拓扑图，对比无状态和有状态应用在 NGINX 层面的实际拓扑差异]

## 2.1 HTTP 负载均衡 (HTTP Load Balancing)

* **核心知识点**：使用 NGINX 的 HTTP 模块控制 HTTP 请求的负载均衡，通过 `upstream` 块定义上游资源池。
* **参数配置要点**：
  * `upstream` 池可混合使用 Unix sockets、IP 地址和服务器主机名。
  * `weight`：**权重参数**。影响特定服务器被分配到的请求比例，如果不指定，默认值为 `1`。
  * `backup`：**备用节点机制**。标记为 backup 的服务器仅在主服务器群全部不可用时，才会被启用以接收流量。
* **后续扩展建议**：[此处可扩展配置 NGINX Plus 专属参数，如连接限制 (connection limits) 或高级 DNS 解析控制]

```nginx
upstream backend {
    server 127.0.0.1:8080 weight=3;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082 backup;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

## 2.2 TCP 负载均衡 (TCP Load Balancing)

* **核心主旨**：使用 `stream` 模块在 TCP 协议级别对数据库（如 MySQL 读取副本）等进行反向代理和负载均衡。
* **核心概念与对比**：
  * `http` 上下文主要在 OSI 模型的第 7 层（应用层）运行，专门解析 HTTP 协议。
  * `stream` 上下文主要在 OSI 模型的第 4 层（传输层）运行，核心职责是对数据包进行路由和负载均衡，默认不具备应用层感知能力。
* **易错细节**：**TCP 配置文件切勿放入 HTTP 专用的 `conf.d` 文件夹**（因该文件夹通常被包括在 `http` 块内）。应创建独立的 `stream.conf.d` 目录，并在顶级配置 `nginx.conf` 中开启 `stream` 块将其 `include` 引入。

```nginx
# nginx.conf 顶级
stream {
    include /etc/nginx/stream.conf.d/*.conf;
}
```

## 2.3 UDP 负载均衡 (UDP Load Balancing)

* **核心知识点**：在 `stream` 模块中通过 `listen` 指令后追加 `udp` 关键字实现（例如针对 NTP 或 DNS 服务的负载均衡）。
* **关键机制 (reuseport)**：
  * **定义**：对于需要在客户端和服务器之间进行多次数据包交互的复杂服务（如 OpenVPN、VoIP 语音、虚拟桌面、DTLS），必须使用 `reuseport` 参数。
  * **底层逻辑**：指示 NGINX 为每个工作进程创建单独的监听套接字，允许内核在工作进程之间平均分配传入的连接。
  * **环境依赖**：此功能需要 Linux 内核版本 3.9 及以上，或 FreeBSD 12 及以上版本。

## 2.4 负载均衡方法 (Load-Balancing Methods)

* **核心主旨**：由于异构工作负载或不同的服务器性能，默认的轮询并不能满足所有场景，NGINX 提供了多种精细化的算法。
* **核心算法拆解**：
  * **Round robin (轮询)**：默认算法。按服务器列表顺序分配，可结合 `weight` 实现统计学加权平均。
  * **Least connections (最少连接, `least_conn`)**：将请求代理至当前拥有**最少活动连接数**的上游服务器，同时支持计算权重。
  * **Least time (最短时间, `least_time`)**：**NGINX Plus 专属**。最先进的算法之一，不仅倾向于最少连接数，同时优先选择**平均响应时间最低**的服务器。需配合 `header` (收到响应头的时间) 或 `last_byte` (收到完整响应的时间) 参数使用。
  * **Generic hash (通用哈希, `hash`)**：通过给定的文本、运行时变量（如客户端 IP）生成哈希键。增减服务器时会导致哈希重分配，可增加 `consistent` 参数缓解重分配带来的影响。
  * **Random (随机, `random`)**：通过带上参数 `two [method]`，指示 NGINX 随机挑选两台服务器，再按照指定方法（如默认的最少连接）二选一，平衡随机性与负载特征。
  * **IP hash (`ip_hash`)**：仅适用于 HTTP。使用 IPv4 的前三个八位字节或完整 IPv6 地址计算哈希。**重点结论**：该方法能确保同一客户端只要上游节点存活，就始终被代理到同一台服务器，完美解决基础会话持久性问题。

```nginx
upstream backend {
    least_conn;              # 或 ip_hash; hash $remote_addr consistent;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
}
```

## 2.5 NGINX Plus 的 Sticky Cookie (Sticky Cookie with NGINX Plus)

* **核心知识点**：将下游客户端绑定到指定上游服务器的高级会话持久化方案。
* **工作机制**：通过在 `upstream` 块中使用 `sticky cookie` 指令，NGINX 会在客户端的首次请求中生成一个 Cookie（包含上游服务器信息），并在后续请求中通过追踪此 Cookie 实现持续路由。支持配置过期时间 (expires)、域名 (domain)、路径 (path)、以及安全标识 (httponly, secure)。

## 2.6 NGINX Plus 的 Sticky Learn (Sticky Learn with NGINX Plus)

* **应用场景**：当后端应用需要自行生成和管理会话 Cookie（如 `jsessionid` 或 `phpsessionid`）时，NGINX 可通过「学习」来追踪会话。
* **内部逻辑与配置**：
  * 利用 `create` 参数检查后端响应头中生成的 Cookie。
  * 利用 `lookup` 参数在后续请求中查找该 Cookie 进行路由定位。
  * 利用 `zone` 参数在共享内存中记录会话映射关系（**案例数据**：1MB 的共享内存区域约可追踪 4,000 个会话）。

## 2.7 NGINX Plus 的 Sticky Routing (Sticky Routing with NGINX Plus)

* **核心知识点**：提供极高粒度的持久会话路由控制。
* **逻辑脉络**：利用多个 `map` 块分别从 Cookie 或 URI 中提取会话标识 → 赋值给变量 → 在 `upstream` 块使用 `sticky route` 指令并行传入多个变量 → **重点结论：NGINX 将按顺序评估，并使用第一个非空或非零变量执行路由**。

## 2.8 NGINX Plus 的连接排空 (Connection Draining with NGINX Plus)

* **关键定义**：**连接排空 (Draining)** 是指优雅移除后端服务器的过程。当服务器打上排空标记后，NGINX 将停止向其发送新的会话，但仍允许目前存在的会话在其生命周期内被正常服务完毕。
* **操作方式**：可通过 NGINX Plus 的 RESTful API 提交包含 `{"drain":true}` 的 PATCH 请求，也可在配置文件中加上 `drain` 参数后重载生效。

## 2.9 被动健康检查 (Passive Health Checks)

* **核心机制**：在所有版本中可用。作为正常客户端请求生命周期的一部分，NGINX **被动地监控**传递过程中的连接失败或超时情况。
* **核心控制参数**：`max_fails`（达到失败次数阈值后判定为不健康，默认 1）和 `fail_timeout`（判定失败和不健康状态维持的时间窗口，默认 10s）。

```nginx
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;
}
```

## 2.10 NGINX Plus 的主动健康检查 (Active Health Checks with NGINX Plus)

* **核心机制**：NGINX 定期脱离客户端请求，主动向上游发起检查以阻断故障。
* **HTTP 探测要点**：通过 `location` 块中的 `health_check` 指令定义。强制只能使用 HTTP `GET` 方法探测（防止其他方法修改后端状态）。利用 `match` 块可以严格比对响应的 `status`（状态码）、`header`（请求头）以及 `body` 包含的内容。
* **TCP/UDP 探测要点**：由于没有 HTTP 语义，通过 `match` 块内的 `send` 指令发出特定原始数据流，再利用 `expect` 校验预期的确切响应或正则匹配结果。

## 2.11 NGINX Plus 的慢启动 (Slow Start with NGINX Plus)

* **应用场景**：为刚刚恢复健康或刚启动的上游服务器进行「预热」。
* **核心结论**：`slow_start` 指令允许服务器被重新引入负载均衡池时，在指定时间周期内**逐步、平滑地增加并发连接数**，从而使应用有足够的时间填充本地缓存或建立数据库连接池，免于崩溃。
* **易错细节**：该功能**严禁**与 `hash`、`ip_hash` 或 `random` 等强一致性/强随机负载均衡算法混合使用。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| upstream | HTTP 层定义后端池；`proxy_pass http://name` |
| weight / backup | 加权分配；主池全挂才用 backup |
| stream | L4 TCP/UDP；独立 `stream.conf.d`，勿放 http conf.d |
| least_conn | 分给活动连接最少的服务器 |
| ip_hash | 同客户端固定上游；基础会话保持 |
| hash + consistent | 一致性哈希，减节点时少抖动 |
| max_fails / fail_timeout | 开源版被动健康检查 |
| Plus 专属 | sticky、主动 health_check、slow_start、drain |
