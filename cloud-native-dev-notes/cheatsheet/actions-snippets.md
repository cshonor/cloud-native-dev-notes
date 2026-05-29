# GitHub Actions 片段速查

## 基本工作流

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Hello"
```

## Docker 构建推送

```yaml
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

## 常用触发器

```yaml
on:
  push:
    branches: [main, develop]
    paths: ['src/**']
  pull_request:
  schedule:
    - cron: '0 0 * * 0'
  workflow_dispatch:
```

## 矩阵构建

```yaml
    strategy:
      matrix:
        node-version: [18, 20]
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
```
