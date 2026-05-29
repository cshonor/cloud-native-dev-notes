# Nginx 配置速查

## 基本结构

```nginx
events { worker_connections 1024; }

http {
    upstream backend {
        server app1:8080;
        server app2:8080;
    }

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## 常用指令

| 指令 | 说明 |
|------|------|
| `listen` | 监听端口 |
| `server_name` | 虚拟主机名 |
| `location` | URL 路由匹配 |
| `proxy_pass` | 反向代理目标 |
| `root` / `alias` | 静态文件路径 |
| `try_files` | 依次尝试文件 |
| `rewrite` | URL 重写 |

## 操作命令

```bash
nginx -t              # 测试配置
nginx -s reload       # 热重载
nginx -s stop         # 停止
```
