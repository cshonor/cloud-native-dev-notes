# 第4章 大规模内容缓存机制 (Massively Scalable Content Caching)

> **后端学习提示**：本章**选学**。了解 `proxy_cache` 概念即可；后端日常更常见的是 CDN/网关层缓存或应用内 Redis，不必深挖 NGINX CDN 运维。与 Ch01 反向代理、`proxy_pass` 配合理解。

## 4.0 引言 (Introduction)

* **核心主旨**：缓存机制通过存储响应内容供未来重复使用，能够显著加速内容分发、减少上游服务器负载并降低带宽消耗。
* **逻辑脉络**：通过在靠近最终用户的战略位置部署多个 NGINX 缓存节点，企业完全可以基于 NGINX 构建属于自己的**内容分发网络 (CDN)**。同时，在后端应用发生故障时，缓存系统可被动地提供历史响应，从而极大增强整体业务可用性。
* **重点结论**：所有缓存相关特性及配置**仅在 `http` 上下文内有效**。

## 4.1 缓存区域定义 (Caching Zones)

* **核心知识点**：使用 `proxy_cache_path` 指令定义用于缓存共享内存及磁盘文件的路径空间。
* **关键参数拆解**：
  * `keys_zone`：定义共享内存区域的名称和分配容量（例如 `keys_zone=main_content:60m` 定义了 60MB 内存用于存放活跃键值和元数据）。
  * `levels`：定义文件系统目录的层级哈希结构（例如 `levels=1:2` 设定两级目录），此举能避免单目录下堆积过多文件导致检索性能骤降。
  * `inactive`：控制指定缓存对象在未被访问后驻留的最长时间（例如 `inactive=3h` 表示三小时无人访问即触发驱逐销毁）。
  * `max_size` 与 `min_free`：前者控制总缓存池允许占用的最大磁盘空间（如 `20g`），后者保证磁盘必须保留的安全空余空间（如 `500m`），一旦触及阈值，NGINX 会依照 LRU 规则清理旧数据。
* **易错细节**：`proxy_cache_path` 指令是全局定义，**只能**在最顶层的 `http` 块中声明；而真正决定某个虚拟主机或路径是否开启缓存的 `proxy_cache` 指令，则可向下渗透并在 `http`、`server` 或 `location` 上下文中使用。

```nginx
# http 块内（全局，仅一次）
proxy_cache_path /var/cache/nginx/main
    levels=1:2
    keys_zone=main_content:60m
    inactive=3h
    max_size=20g
    min_free=500m;

server {
    location / {
        proxy_cache main_content;
        proxy_pass http://backend;
    }
}
```

## 4.2 缓存哈希键设计 (Caching Hash Keys)

* **核心概念**：通过 `proxy_cache_key` 指令定义构成特定缓存对象唯一标识的哈希拼接字符串。
* **配置对比与逻辑关联**：
  * **默认配置**：`"$scheme$proxy_host$request_uri"`（即基于 HTTP 协议、代理目标主机和请求路径计算哈希）。对于大多纯静态资源而言，默认规则已完全适用。
  * **动态内容进阶配置**：当面对高度动态的内容（如用户主页、仪表盘等），不同用户请求的路径 (URI) 完全相同但内容千差万别。此时**必须引入业务变量**重定义缓存键，例如加入识别用户的 Cookie、Session ID 或 JWT 字段：`"$host$request_uri $cookie_user"`。
* **易错细节与风险提示**：在缓存动态应用数据时，若哈希键选取不够精确（例如遗漏了区分用户的核心凭证），将导致严重的串号越权越界安全事故（如将 A 用户的私密信息错误地呈现给 B 用户）。

```nginx
# 静态资源：默认键即可
# proxy_cache_key "$scheme$proxy_host$request_uri";

# 动态/用户相关：必须加入用户标识
proxy_cache_key "$host$request_uri$cookie_sessionid";
```

## 4.3 缓存并发锁定 (Cache Locking)

* **核心主旨**：用于防御**缓存击穿**问题，管控当出现海量并发请求冲击某一未命中/已失效的缓存节点时，NGINX 对后端服务器的调度保护机制。
* **参数逻辑体系**：
  * `proxy_cache_lock on;`：开启并发写锁。同一时刻仅允许一个代理请求穿透去访问后端以回填缓存，其余后续相同资源的请求直接在 NGINX 队列中等待，待回填完毕后直接读取缓存响应。
  * `proxy_cache_lock_age`：设置「带头回填请求」的处理宽限时间（默认 5 秒）。若该请求超时未能完成回填，NGINX 会释放并发锁，允许另一个请求去源站尝试抓取数据。
  * `proxy_cache_lock_timeout`：设定客户端在 NGINX 处最长的等待忍耐时间（默认 5 秒）。如果等待超时，这些被挂起的请求将直接绕过写入锁访问上游应用，获取到数据后自行返回给客户端，且**不负责回填缓存**。

```nginx
location /api/ {
    proxy_cache_lock on;
    proxy_cache_lock_age 5s;
    proxy_cache_lock_timeout 5s;
    proxy_pass http://backend;
}
```

## 4.4 启用陈旧缓存 (Use Stale Cache)

* **应用场景**：这是一种极其重要的容灾降级兜底方案。当上游应用服务出现崩溃断联时，NGINX 可主动为客户端派发虽已过期但在磁盘内留存的**陈旧（Stale）数据**。
* **核心配置要点**：通过 `proxy_cache_use_stale` 指令定义触发兜底行为的异常条件，包含：`error`（根本无法连通上游）、`timeout`（上游响应超时）、`invalid_header`（上游返回非法头信息）、`updating`（后台有其他请求正在刷新该缓存时，避免阻塞并发读取），以及一系列网关层错误码（`http_500`, `http_502`, `http_503`, `http_504` 等）。

```nginx
proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
```

## 4.5 缓存绕过机制 (Cache Bypass)

* **核心主旨**：赋予 NGINX 根据特定上下文动态判断是否忽略读取既有缓存，强制回源提取最新数据的能力。通常用于技术排障调试或强制刷新特定视图。
* **配置机制**：使用 `proxy_cache_bypass` 指令，并传入一系列探测变量（如请求头、Cookie 参数）。**判定逻辑**：只要传入的参数序列中存在任何一个**不为空 (non-empty) 且不等于零 (non-zero)** 的值，缓存匹配阶段即被绕过。
  * **案例应用**：客户端通过发送特制 Header（如 `proxy_cache_bypass $http_cache_bypass;`），直接越过代理层缓存直达核心应用池。
* **重点结论**：若需针对某个 `location` 彻底不使用缓存，切勿滥用本指令，而是直接声明 `proxy_cache off;`。

```nginx
proxy_cache_bypass $http_cache_bypass;
proxy_no_cache $http_cache_bypass;
```

## 4.6 NGINX Plus 缓存主动清理 (Cache Purging with NGINX Plus)

* **核心功能**：专门提供接口使特定过时缓存条目失效，确保 CDN 内容一致性（该特性为 NGINX Plus 专有）。
* **操作模式与限制**：
  * 通过自定义 `map` 指令绑定请求方法。例如，拦截 HTTP 动作 `PURGE` 并将其转换为开启标识（设为 `1`），然后传入 `proxy_cache_purge` 执行动作清理目标文件。
  * **进阶拓展**：若在配置根 `proxy_cache_path` 时追加了 `purger=on` 参数，清理功能支持输入星号 (`*`) 尾缀，进行通配符路径的批量范围清除（例如针对全目录强制下线）。
  * **安全规范**：清理接口非常危险，不可暴露在公网，务必结合 IP 黑白名单模块 (`geoip`) 或基本验证规则 (`auth_basic`) 严加保护。

## 4.7 缓存切片技术 (Cache Slicing)

* **核心主旨**：用于极大地提升大型不常变动资源（例如 HTML5 视频伪流传输、大体量安装包）的缓存与传输利用率。
* **原理脉络与执行过程**：
  * 使用 `slice` 指令指定固定分块大小（例如 `slice 1m;` 定义切分片段为 1MB）。
  * 当遇到针对大体积文件的 Byte-Range 并发请求或跨块提取请求时，NGINX 会向上游服务器分批次发送单独针对具体片层范围（Range）的子请求。
  * 各个子请求返回的数据段独立缓存并入库。一旦所有需求片段到达，NGINX 拼接完整响应输出给客户端，极大避免重复下载完整庞大文件的昂贵开销。
* **格式硬性规则依赖**：
  1. 必须在缓存哈希键 (`proxy_cache_key`) 中嵌入 NGINX 内置切片片段范围变量 `$slice_range`。
  2. 必须重写上游请求头传入切割边界：`proxy_set_header Range $slice_range;`。
  3. 代理请求必须显式指定升级到 **HTTP/1.1 协议**（`proxy_http_version 1.1;`），因为基础的 1.0 协议语义并不支持请求范围传递。
* **易错细节**：切片高度依赖源站的静态一致性校验。NGINX 接受每个片段时均比对实体标签 (`ETag`)。若源站动态改变了该文件造成 `ETag` 波动，所有缓存注入操作会立即因验证异常而中止。对于体积小或变化频次高的文件，不应开启本切片优化，而直接回退采用并发锁定策略 (`proxy_cache_lock`)。

```nginx
slice 1m;
proxy_cache_key $uri$is_args$args$slice_range;
proxy_set_header Range $slice_range;
proxy_http_version 1.1;
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| proxy_cache_path | 仅在 `http` 块定义缓存区 |
| proxy_cache | 在 server/location 启用缓存 |
| proxy_cache_key | 缓存唯一键；动态内容须含用户标识 |
| proxy_cache_lock | 防击穿：同时仅一个回源回填 |
| proxy_cache_use_stale | 上游故障时返回过期缓存 |
| proxy_cache_bypass | 非空非零变量 → 跳过缓存读 |
| proxy_cache off | 某 location 彻底不用缓存 |
| slice | 大文件分片缓存；需 HTTP/1.1 + Range |
| 安全 | 动态缓存键不精确 → 用户数据串号 |
