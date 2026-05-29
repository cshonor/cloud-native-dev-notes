# 第5章 可编程性与自动化 (Programmability and Automation)

> **后端学习提示**：本章**跳过** ⏭️。NGINX Plus API、njs、Ansible/Chef/Consul 属运维/平台向；后端只需知道「配置可动态化、可 IaC」，日常用 K8s Ingress annotation 或 GitOps 即可。

## 5.0 引言 (Introduction)

* **核心主旨**：本章深入探讨通过编程和自动化工具来管理与交互 NGINX 的高级能力。
* **逻辑脉络**：
  * **可编程性 (Programmability)**：通过 HTTP 接口（NGINX Plus 专有 API）动态修改配置、添加/移除上游服务器，以及利用键值存储（Key-Value Store）实现动态路由与流量控制。
  * **自动化 (Automation)**：现代云原生架构下，运维人员通过配置管理工具（如 Ansible、Chef、Consul）编写代码，实现服务器的自动化、模块化安装和动态模板渲染。
* **预留拓展空间**：[可在此补充当前企业内部 CI/CD 流程中集成的自动化部署工具链架构图]

## 5.1 NGINX Plus API

* **核心知识点**：NGINX Plus 提供了原生的 **RESTful API**，允许在不重载 (Reload) 服务的情况下，通过 HTTP 请求对系统行为和配置进行动态读写。
* **配置要点与权限控制**：
  * 通过 `api write=on;` 指令在特定的 `location` 块中开启 API 的读写权限。
  * **易错细节**：必须严格限制对 API 端点的访问权限，强烈建议配置适当的访问控制（参考第7章安全控制）。
* **RESTful 交互规范与操作逻辑**：
  * **添加节点**：通过 `POST` 请求向 `/api/{version}/http/upstreams/{httpUpstreamName}/servers/` 提交 JSON 格式的 Server 配置，即可将新服务器加入上游池。
  * **获取列表**：通过对同上 URI 发起 `GET` 请求，可以获取整个资源池节点的 JSON 数组（包含节点的自动生成的 `id` 及各类负载均衡参数）。
  * **连接排空 (Connection Draining)**：在移除节点前，对其 ID 发起带有 `{"drain":true}` 的 `PATCH` 请求，**重点结论：NGINX 会停止向该节点发送新请求，直到其现有会话全生命周期结束，实现优雅下线**。
  * **移除节点**：在节点排空后，通过向特定 ID 的 URI 发起 `DELETE` 请求将其彻底从配置池中删除。
* **应用场景**：这使得基础设施能够结合外部监控或弹性伸缩组，在无人工干预的情况下自动扩缩容。

```nginx
location /api/ {
    api write=on;
    # 必须配合 allow/deny 或 auth 限制访问
}
```

## 5.2 使用 NGINX Plus 的键值存储 (Using the Key-Value Store with NGINX Plus)

* **核心功能**：通过 API 暴露的一块共享内存区域，使得应用程序可以将数据注入 NGINX Plus 中，作为其实时流量管理的判定依据。
* **配置逻辑**：
  * 使用 `keyval_zone` 指令定义共享内存空间的大小与名称。
  * 使用 `keyval` 指令将键（例如客户端 IP `$remote_addr`）映射到值变量中。
* **操作案例（动态黑名单）**：
  * 发起 `POST` 请求 `{"127.0.0.1":"1"}` 写入黑名单键值对后，NGINX 会将收到的值赋给内部变量 `$blocked`。
  * 利用 `if ($blocked)` 执行 `return 403;` 拦截流量。
  * 通过 `PATCH` 请求将对应 IP 的值设为 `null` 即可将其移出黑名单。
* **进阶特性**：
  * **集群感知 (Cluster-aware)**：从 R16 版本起，向任一节点更新的键值会自动同步到整个 NGINX Plus 集群中。
  * **类型索引 (Type Indexing)**：引入 `type` 参数，除默认的 `string`（精确匹配）外，支持 `prefix`（前缀匹配）和 `ip`（CIDR 网段匹配），极大增强了网段级管控能力。

## 5.3 使用 njs 模块暴露 NGINX 内的 JavaScript 功能

* **核心主旨**：利用广泛使用的 JavaScript 语言，通过 NGINX JavaScript (njs) 模块在代理层嵌入高级业务逻辑处理请求与响应。
* **安装与配置依赖**：需要通过包管理器安装 `nginx-module-njs` 或 `nginx-plus-module-njs`。
* **实现逻辑与案例（JWT 拆解解析）**：
  * **分离业务逻辑**：在独立的 `.js` 文件中编写 JavaScript 函数（例如，解析 HTTP 头中的 Authorization 字段截断前缀，进行 base64url 解码并解析 JSON，以提取 JSON Web Token 中的 `sub` 与 `iss` 字段）。
  * **模块引入与变量映射**：在 `http` 块中使用 `js_path` 定义路径，通过 `js_import` 导入 js 文件，并使用 `js_set` 指令将执行结果映射为 NGINX 变量。
  * **实际调用**：随后在 `server` 的路由配置中直接通过内置变量（如 `$jwt_payload_subject`）引用函数处理后的数据并控制路由或响应。

```nginx
js_import jwt.js;
js_set $jwt_subject jwt.get_subject;

location /api/ {
    # 可用 $jwt_subject 做路由或鉴权
    proxy_pass http://backend;
}
```

## 5.4 使用通用编程语言扩展 NGINX (Extending NGINX with a Common Programming Language)

* **核心知识点**：除原生的 C 语言模块外，NGINX 也支持动态加载其他常见脚本语言，如 Lua、Perl 模块，利用其丰富的社区资源进行扩展。
* **技术路线对比**：
  * **Lua**：通过加载 `ngx_http_lua_module.so`，可使用 `content_by_lua_block` 直接在配置内嵌入代码，模块暴露了专属的 `ngx` 对象，用于操作请求体或构造响应。
  * **Perl**：通过加载 `ngx_http_perl_module.so`，使用 `perl_set` 执行 Perl 脚本来生成配置变量（例如：读取服务器的底层 OS 环境变量并将其用作动态代理寻址 `$APP_DNS_ENDPOINT`）。

| 扩展方式 | 语言 | 典型场景 |
|----------|------|----------|
| njs | JavaScript | JWT 解析、轻量逻辑 |
| Lua (OpenResty) | Lua | API 网关、复杂路由 |
| Perl | Perl | 动态变量生成 |

## 5.5 使用 Ansible 安装 (Installing with Ansible)

* **核心知识点**：**Ansible** 是基于 Python 编写的配置管理工具，通过 YAML 定义任务、Jinja2 引擎执行模板化，以 SSH 方式批量应用到目标节点。
* **架构脉络与实现方案**：
  * **依赖准备**：从 Ansible Galaxy 拉取官方维护的集合包 `nginxinc.nginx_core`。
  * **Playbook 结构**：使用官方内置的 `nginx` 角色完成 NGINX 安装，使用 `nginx_config` 角色控制配置写入。
  * **配置覆盖 (Variables Overrides)**：在变量 `vars` 块内，定义监听端口、服务器名、日志路径及根目录，模块将自动将其渲染为 `default.conf`，彻底实现配置即代码（Configuration as Code）。
* **预留拓展空间**：[可在此补充 F5 提供的针对 NGINX App Protect WAF 的专属 Ansible 自动化配置参数]。

## 5.6 使用 Chef 安装 (Installing with Chef)

* **核心知识点**：**Chef** 是基于 Ruby 语言的自动化平台，主要使用 Supermarket 中发布的公共 Cookbook（由 Sous Chefs 社区维护）进行资源管理。
* **自动化拆解步骤**：
  * **导入资源**：利用 `knife` 工具安装 nginx cookbook，并在自有配方 (recipe) 中声明其依赖。
  * **环境安装**：通过 `nginx_install` 资源块结合参数 `source 'repo'`，从官方源获取最新包并安装。
  * **全局参数定义**：使用 `nginx_config` 资源块声明全局参数（如 worker_processes，keepalive_timeout 等），并利用 Chef 通知机制（`notifies :reload`）重载服务。
  * **虚拟站点模板**：通过 `nginx_site` 资源块声明具体 Server 块配置，其内部的 `variables` 将直接被解析生成 `.conf` 配置文件。

## 5.7 使用 Consul 模板实现配置自动化 (Automating Configurations with Consul Templating)

* **核心概念**：**Consul** 是分布式的服务发现与配置存储平台，结合 `consul-template` 守护进程，可基于事件驱动让 NGINX 配置「活起来」。
* **工作机制与逻辑闭环**：
  * **模板语法**：编写 `.template` 后缀文件，利用内部语法块 `{{range service "app.backend"}} server {{.Address}};{{end}}`，遍历当前在 Consul 注册且健康的后端服务节点，将其 IP 插入为 NGINX `server` 参数。
  * **事件驱动守护**：通过 CLI 运行 `consul-template` 指向 Consul 集群及本地模板。
  * **自动重载**：**关键结论**：一旦后端节点数量由于弹性扩容或故障而改变，该守护进程将自动重绘目标 `upstream.conf` 文件，并立即执行钩子命令 `"nginx -s reload"`，实现流量分配池的无缝平滑自愈更新。

```
Consul 服务注册变化
    → consul-template 重渲染 upstream.conf
    → nginx -s reload
    → upstream 池自动更新
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| NGINX Plus API | REST 动态改 upstream，无需 reload |
| drain PATCH | 优雅下线：停新连接，等旧会话结束 |
| Key-Value Store | API 写 IP 黑名单等，实时生效 |
| njs | 配置内嵌 JS 逻辑（JWT 解析等） |
| Lua / Perl | OpenResty 等更重扩展方案 |
| Ansible / Chef | IaC 批量安装与渲染 nginx.conf |
| consul-template | 服务发现驱动 upstream + 自动 reload |
| 后端替代 | K8s Service/Ingress + GitOps |
