# 第1章 基础知识 (Basics)

> **后端学习提示**：本章**必学** ⭐。掌握安装、`nginx.conf` 层级、`nginx -t`/reload、`server`/`location`/`root`/`proxy_pass` 基础；后续 Ch02/Ch03/Ch07 都建立在本章之上。

## 1.0 引言 (Introduction)

* **核心主旨**：开始使用 NGINX 开源版或 NGINX Plus 的第一步是环境安装与基础配置。了解如何安装服务、定位主配置文件、掌握系统管理命令，并学会如何验证安装及向默认服务器发起请求。
* **预留拓展空间**：[可在此补充企业内部统一初始化规范、定制化编译安装（Compile from source）的相关流程说明，或自动化安装脚本锚点]

## 1.1 在 Debian/Ubuntu 上安装 NGINX (Installing NGINX on Debian/Ubuntu)

* **核心知识点**：通过高级包管理工具 (APT) 和 NGINX 官方存储库安装 NGINX。
* **逻辑脉络与配置要点**：
  * **安装依赖包**：需要先安装 `curl`、`gnupg2`、`ca-certificates`、`lsb-release` 等依赖包，以辅助配置 NGINX 官方仓库。
  * **添加并信任签名密钥**：必须下载 NGINX GPG 包签名密钥（nginx_signing.key），这允许 APT 系统在安装时验证官方存储库包的合法性。
  * **自动提取环境变量**：利用 `lsb_release` 命令自动提取操作系统名称 (`OS`) 和发布版本代码 (`RELEASE`) 以配置对应的 APT 数据源，这种机制可兼容不同发行版的 Debian 或 Ubuntu，避免人为输入错误。
  * **启动与自启**：安装后需执行 `systemctl enable nginx` 开启开机自启，并运行 `nginx` 启动服务。

```bash
sudo apt-get update
sudo apt-get install -y curl gnupg2 ca-certificates lsb-release
# 按官方文档添加 nginx.org 仓库后：
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 1.2 通过 YUM 包管理器安装 NGINX (Installing NGINX Through the YUM Package Manager)

* **适用场景**：适用于 Red Hat Enterprise Linux (RHEL)、Oracle Linux、AlmaLinux、Rocky Linux 或 CentOS。
* **操作逻辑**：
  * **创建存储库文件**：在 `/etc/yum.repos.d/nginx.repo` 中直接写入官方存储库 URL 及配置规则。
  * **易错细节（防火墙阻断）**：安装并启动 NGINX 后，**必须在系统防火墙中放行 HTTP 默认的 TCP 80 端口**（使用 `firewall-cmd --permanent --zone=public --add-port=80/tcp`），否则客户端请求会被直接拦截；修改完成后需通过 `--reload` 参数重载防火墙使配置生效。

```bash
sudo firewall-cmd --permanent --zone=public --add-port=80/tcp
sudo firewall-cmd --reload
```

## 1.3 安装 NGINX Plus (Installing NGINX Plus)

* **关键定义**：NGINX Plus 的安装指令虽与开源版相似，但存在强制的商业身份验证流程。
* **核心差异**：必须先从 NGINX 门户获取合法的**证书 (certificate)**和**密钥 (key)**，并提供给操作系统，以便系统在访问 NGINX Plus 存储库时完成身份验证。

## 1.4 验证安装 (Verifying Your Installation)

* **核心指令与诊断逻辑**：
  * **版本检查**：执行 `nginx -v` 直接输出当前安装的 NGINX 版本号。
  * **进程检查**：执行 `ps -ef | grep nginx`。**重点结论**：正常运行的 NGINX 服务必定包含一个 **master 进程**和至少一个 **worker 进程**。
  * **权限解析**：master 进程默认必须以 **root 权限**运行，因为 NGINX 需要提升的系统特权才能正常工作（例如绑定小于 1024 的 80 特权端口）。
  * **连通性测试**：使用 `curl localhost`（或主机的 IP / 域名）发起 HTTP 请求，验证 NGINX 的默认 HTML 欢迎站点是否可以正常返回内容。

```bash
nginx -v
ps -ef | grep nginx
curl -I localhost
```

## 1.5 关键文件、目录和命令 (Key Files, Directories, and Commands)

* **核心目录与文件网络**：
  * `/etc/nginx/`：NGINX 服务器的默认配置根目录，存放决定服务行为的核心文件。
  * `/etc/nginx/nginx.conf`：NGINX 守护进程的**默认配置入口点**，包含配置工作进程、系统调优、日志、动态模块的全局设置，并包含顶级的 `http` 块。
  * `/etc/nginx/conf.d/`：包含默认 HTTP 服务器配置文件的目录（以 `.conf` 结尾）。**易错细节**：某些包管理库习惯使用 `sites-enabled` 和 `site-available` 文件夹的软链接约定，**该规范目前已被弃用 (deprecated)**。最佳实践是使用 `include` 将 `conf.d/` 目录引入。
  * `/var/log/nginx/`：默认日志存储位置。核心包含记录所有客户端请求的 `access.log` 和记录错误及调试信息的 `error.log`。
* **关键命令速查**：
  * `nginx -V`：显示版本、底层构建信息及配置参数，用于排查**编译进入 NGINX 二进制文件的具体模块**。
  * `nginx -t` 与 `nginx -T`：测试配置文件语法。**实用要点**：大写的 `-T` 不仅测试配置，还会将验证后的完整配置参数打印至终端，在排障和寻求技术支持时具有极高的价值。
  * `nginx -s [signal]`：通过 `-s` 参数向 master 进程发送核心管理信号。包括：`stop`（立即强制中断）、`quit`（优雅停止，处理完毕飞行中的请求后再中断）、`reload`（无缝重载配置）、`reopen`（重新打开系统日志文件）。

```
/etc/nginx/nginx.conf          # 主配置入口
    ├── http { ... }
    │     └── include conf.d/*.conf
    └── /var/log/nginx/
          ├── access.log
          └── error.log
```

## 1.6 使用 Include 保持配置整洁 (Using Includes for Clean Configs)

* **核心主旨**：通过模块化拆分，避免出现单一配置文件长达数百行导致难以维护的局面。
* **机制脉络**：`include` 指令在任何配置上下文中均有效，可接收具体的单一文件路径，或匹配多个文件的掩码（例如 `ssl_config/*.conf`）。
* **实用场景与案例**：当管理同一服务器上的多个 FastCGI 虚拟服务器，或配置多个依赖相似 SSL/TLS 证书规则的站点时，应将这些公共逻辑编写为独立文件，利用 `include` 引入。这能彻底杜绝配置代码重复，确保整体架构整洁稳固。

```nginx
# nginx.conf
http {
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/ssl_config/*.conf;
}
```

## 1.7 提供静态内容服务 (Serving Static Content)

* **核心知识点**：通过覆盖或配置默认的 HTTP 服务器块（`/etc/nginx/conf.d/default.conf`），实现基于指定目录的静态文件下发。
* **参数配置要点拆解**：
  * `listen 80 default_server;`：**关键机制**：声明服务监听 80 端口。`default_server` 参数极为关键，它指示 NGINX，如果 HTTP 请求的 Host 标头未能匹配到任何明确指定的 `server_name`，则默认由该 `server` 块接管兜底处理请求。
  * `server_name`：定义期望被路由到此上下文的主机名（域名）。如果已设置 `default_server` 且暂无域名，此项可省略。
  * `location /`：根据请求的统一资源标识符 (URI) 进行配置匹配，`/` 代表匹配一切访问路径。
  * `root` 指令：**逻辑脉络**：向 NGINX 指明静态文件在系统中的绝对基础路径。当检索文件时，**请求的完整 URI 路径会被自动追加到 `root` 指令指定的路径末尾**（注：需区分它与 `alias` 指令对 URI 追加行为的不同处理方式）。
  * `index` 指令：当请求指向一个目录而非具体文件时，提供默认拉取的后备文件列表（例如依次检索 `index.html` `index.htm`）。

```nginx
server {
    listen 80 default_server;
    server_name _;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
    }
}
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| master / worker | 一 master（root）+ 多 worker 处理请求 |
| nginx.conf | 全局入口；含 `http` 块 |
| conf.d/ | 推荐用 `include` 引入站点配置 |
| nginx -t / -T | 语法检查；`-T` 打印完整生效配置 |
| nginx -s reload | 无缝重载配置 |
| default_server | Host 不匹配时的兜底 server |
| root | URI 追加到 root 路径后找文件 |
| index | 目录请求时默认文件名列表 |
