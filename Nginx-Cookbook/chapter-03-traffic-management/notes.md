# 第3章 流量管理 (Traffic Management)

> **后端学习提示**：本章**必学** ⭐。重点掌握 `split_clients`（金丝雀）、`limit_conn`/`limit_req`/`limit_rate` 限流，以及 `geoip2` + `map` 做地域控制；与 Ch07、Ingress annotation 高度相关。

## 3.0 引言 (Introduction)

* **核心主旨**：NGINX 是强大的 Web 流量控制器。本章探讨按照百分比分割流量、基于客户端地理位置控制路由，以及连接、速率、带宽层面的深层次节流控制。

## 3.1 A/B 测试 (A/B Testing)

* **核心知识点**：使用 `split_clients` 模块对用户的特征字符串（如 IP 地址）进行哈希运算并按指定的比例分割，赋值给新变量，极其适用于**金丝雀发布 (Canary Release)** 和**蓝绿部署 (Blue-Green Deployment)**。
* **格式要求**：`split_clients "${remote_addr}AAA" $variant { 20.0% "backendv2"; * "backendv1"; }`。**星号 (`*`) 是固定语法，代表扣除明确百分比后剩余的全部流量池**。

```nginx
split_clients "${remote_addr}AAA" $variant {
    20.0%  backend_v2;
    *      backend_v1;
}

server {
    location / {
        proxy_pass http://$variant;
    }
}
```

## 3.2 使用 GeoIP 模块和数据库 (Using the GeoIP Module and Database)

* **逻辑脉络**：安装特定包管理器对应的动态模块 (`nginx-module-geoip` 或 `nginx-plus-module-geoip2`) → 下载 MaxMind 的城市/国家数据库 (.mmdb) → 使用 `load_module` 挂载 → 在 HTTP/Stream 块中使用 `geoip2` 指令载入数据库文件。
* **产出价值**：将地理数据绑定到 NGINX 内部变量中（如 `$geoip2_data_country_code` 返回两位国家代码），可直接应用于访问控制或后端业务逻辑传递。

## 3.3 基于国家/地区的访问限制 (Restricting Access Based on Country)

* **核心组合用法**：结合 `map` 模块与 `geoip2` 变量构建布尔开关。
* **逻辑脉络**：用 `map` 指令检查国家代码变量 → 符合特定国家（如 "US"）设为 0，否则设为 1（通过 `default` 设置） → 在 `server` 块内用 `if` 指令判定变量若为 1 则直接返回 `403` 拦截。

```nginx
map $geoip2_data_country_code $blocked {
    default 1;
    US      0;
}

server {
    if ($blocked) {
        return 403;
    }
}
```

## 3.4 查找原始客户端 IP (Finding the Original Client)

* **应用场景**：如果 NGINX 前方有云端负载均衡器（如 AWS ELB / GCP LB），NGINX 获取的 IP 会变成代理节点的 IP。
* **核心配置**：
  * `geoip2_proxy`：定义代理服务器（已知负载均衡器）的 CIDR 范围，告知 NGINX 当连接来自此范围时，信任并使用 `X-Forwarded-For` 头。
  * `geoip2_proxy_recursive on;`：启用递归解析，从 `X-Forwarded-For` 中逐层剥离代理 IP，最终穿透找出真实的客户端源 IP。

```nginx
# 通用做法（无 GeoIP 时）
set_real_ip_from 10.0.0.0/8;
real_ip_header X-Forwarded-For;
real_ip_recursive on;
```

## 3.5 限制连接数 (Limiting Connections)

* **核心机制**：用于防止恶意攻击及确保资源分配公平。通过 `limit_conn_zone` 声明共享内存区域，使用 `limit_conn` 在具体上下文中执行拦截。
* **易错细节与最佳实践**：
  * 若使用 `$binary_remote_addr` (IP) 作为限制键，需警惕处于同一 NAT (网络地址转换) 后的所有用户会被视作单一对象而误伤。
  * 拦截返回码 `limit_conn_status` 默认为 `503` (服务端不可用)，**重点建议**：改写为 `429` (Too Many Requests)，因本质上属于客户端请求异常。
  * 可以通过设置 `limit_conn_dry_run on;` 进行无破坏的试运行，分析日志变量 `$limit_conn_status`，精准调试限流阈值后再实际上线。

```nginx
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
limit_conn_status 429;

server {
    limit_conn conn_limit 10;
}
```

## 3.6 限制速率 (Limiting Rate)

* **核心机制**：用于防止基于高频抓取或暴力破解类型的滥用。使用 `limit_req_zone` 设定如 `rate=3r/s` 的固定速率处理限制。
* **高级两段式速率限制 (Two-stage Rate Limiting)**：
  * **Burst 参数**：允许超过设定速率的突发请求数在缓冲区「排队」而不被立刻拒绝。
  * **Delay / Nodelay 参数**：`nodelay` 允许缓冲区内的突发请求立刻被消费处理而没有延迟；若不加此参数，或使用 `delay={num}`，NGINX 会受控地对超出速率范围的请求进行降速节流（按限制速率逐个处理），直至队列超出界限被最终拒绝。

```nginx
limit_req_zone $binary_remote_addr zone=req_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=req_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

## 3.7 限制带宽 (Limiting Bandwidth)

* **核心机制**：在连接维度控制对客户端文件或响应的传输吞吐量。
* **典型配置**：
  * `limit_rate_after 10m;`：核心体验保障手段，在下载前 `10MB` 期间满速传输（保证视频秒开或基础数据快速呈现）。
  * `limit_rate 1m;`：当数据传输突破阈值后，强制将向该客户端的发送速率压降到每秒 `1MB`。
* **注意点**：带宽限速是针对**单条连接**生效的，为防止多线程下载工具规避限制，强烈建议将带宽限流 (`limit_rate`) 结合连接数限流 (`limit_conn`) 同时配置。

```nginx
location /download/ {
    limit_rate_after 10m;
    limit_rate 1m;
}
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| split_clients | 按 IP 哈希比例分流；`*` = 剩余流量 |
| geoip2 + map | 国家代码 → 布尔开关 → 403 |
| real_ip / geoip2_proxy | 穿透 LB 获取真实客户端 IP |
| limit_conn_zone | 限制并发连接数；建议返回 429 |
| limit_req_zone | 限制请求速率；burst + nodelay 处理突发 |
| limit_rate | 单连接带宽限速；配合 limit_conn 防多线程绕过 |
| dry_run | 限流试运行，先打日志再上线 |
