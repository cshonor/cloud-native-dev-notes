# 第13章：高级工作流技术 (Advanced Workflow Techniques)

> **后端学习提示**：本章**选学**。重点 **13.2 矩阵**（多版本 Go/Node 并发构建）和 **13.3 容器 services**（集成测试连 MySQL/Redis）；13.1 驱动 GitHub API 按需查阅。

## 13.1 在工作流中驱动 GitHub (Driving GitHub from Your Workflow)

* **核心主旨**：脱离常规操作的局限，通过多种底层接口直接在工作流内部与 GitHub 组件交互并驱动其功能执行。
* **核心知识点与实现途径**：

| 途径 | 适用场景 | 认证方式 |
|------|----------|----------|
| `gh` CLI | 快速创建 Issue/PR、查状态 | `GITHUB_TOKEN` |
| `actions/github-script` | 复杂 REST 调用、脚本逻辑 | 内置 `github` 客户端 |
| `curl` + REST API | 不依赖额外 Action | `PAT` 或 `GITHUB_TOKEN` |

1. **使用 GitHub CLI (`gh`)**：
   * **逻辑脉络**：GitHub 托管的运行器默认预装了 `gh` 命令行工具。可以直接在 `run` 步骤中调用它（如 `gh issue create`）。
   * **语法要点**：必须通过环境变量显式传递 **`GITHUB_TOKEN`** 授权，例如 `env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`。通过管道和文本处理工具（如 `cut`）可截取命令返回的动态数据（如新创建的 Issue 编号）并写入 `$GITHUB_OUTPUT`。

```yaml
- name: Create issue via gh
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    ISSUE_URL=$(gh issue create --title "CI failed" --body "See logs")
    ISSUE_NUM=$(echo "$ISSUE_URL" | cut -d'/' -f5)
    echo "number=$ISSUE_NUM" >> "$GITHUB_OUTPUT"
  id: issue
```

2. **使用 github-script 动作 (Creating Scripts)**：
   * **关键定义**：官方提供的 `actions/github-script` 允许开发者直接在工作流中编写和执行 JavaScript/Node.js 脚本。
   * **内部对象**：该动作自动提供预认证的 **`github`** 对象（octokit/rest.js 客户端）和包含运行数据的 **`context`** 对象，使得脚本调用 GitHub REST API 变得极其简便。

```yaml
- uses: actions/github-script@v7
  with:
    script: |
      const issue = await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: 'Auto-created from workflow',
        body: `Run: ${context.runId}`
      });
      core.setOutput('number', issue.data.number);
```

3. **调用 GitHub API (Invoking GitHub APIs)**：
   * **实现机制**：如果不想依赖额外的 Action 或 CLI，可直接使用 `curl` 命令行工具发送 HTTP 请求访问 GitHub REST API。
   * **配置细节**：需要在请求头 (Header) 中附加身份验证信息：`Authorization: Bearer ${{ secrets.PAT }}`，并可通过 `jq` 等工具解析返回的 JSON 数据。

```yaml
- run: |
    curl -s -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
      https://api.github.com/repos/${{ github.repository }}/issues \
      | jq '.[0].number'
```

* **预留拓展补充空间**：
  * *【拓展方向】：可进一步探讨 `github-script` 中提供的高级包（如 `@actions/glob` 和 `@actions/io`）在复杂文件系统操作中的实战应用*。

## 13.2 使用矩阵策略自动创建作业 (Using a Matrix Strategy to Automatically Create Jobs)

* **核心主旨**：通过定义多个数据维度的数组，自动展开并生成多个同构作业，以覆盖多环境、多版本或多系统的并发测试与构建需求。
* **关键定义与逻辑脉络**：
  * **一维矩阵 (One-Dimensional Matrices)**：在 `strategy: matrix:` 下定义单个数组（如 `prod: [prod1, prod2]`），系统将按数组元素数量动态生成对应数量的作业。
  * **多维矩阵 (Multi-dimensional Matrices)**：定义两个或以上的数组（如 `prod` 和 `level`），GitHub 将计算这些维度的**笛卡尔积**。例如 2 个 product 乘 3 个 level，会自动派生出 6 个唯一的并发作业组合。
  * **动态上下文矩阵**：矩阵的值不必硬编码，可通过上下文有效载荷（如 `${{ github.event.client_payload.levels }}`）在运行时由外部触发事件动态注入。
* **核心控制指令（包含与排除）**：
  * **`include`（包含额外值）**：用于向矩阵中追加特定的属性，或添加不符合标准笛卡尔积模式的独立新组合（例如：追加一个仅在特定环境下运行的 `alpha` 版本测试）。
  * **`exclude`（排除值）**：用于剔除不需要执行的特定组合（例如：排除某个操作系统与某个特定语言版本的兼容性测试分支），只需声明维度组合或单一维度即可批量过滤。
* **异常控制规则与公式要点 (Handling Failure Cases)**：
  * **`fail-fast`**：作用于矩阵级别。默认值为 `true`（只要有一个矩阵作业失败，立即取消所有仍在排队或运行的其他矩阵作业）。设为 `false` 可允许剩余作业继续执行完。
  * **`continue-on-error`**：作用于单个作业或步骤。即使此组合失败，也不会将其标记为最终失败，从而不触发矩阵层面的 `fail-fast` 拦截机制。
  * **`max-parallel`**：显式限制可同时运行的最大矩阵作业数，防止并发请求对后端基础架构（如自建测试数据库）造成压垮性冲击。

```yaml
jobs:
  test:
    strategy:
      fail-fast: false
      max-parallel: 3
      matrix:
        go: ['1.21', '1.22', '1.23']
        os: [ubuntu-latest, windows-latest]
        exclude:
          - go: '1.21'
            os: windows-latest
        include:
          - go: '1.22'
            os: ubuntu-latest
            coverage: true
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go }}
      - run: go test ./...
```

| 控制项 | 作用域 | 默认值 | 后端场景 |
|--------|--------|--------|----------|
| `fail-fast` | 矩阵 | `true` | 多版本构建设 `false` 看全量结果 |
| `continue-on-error` | 作业/步骤 | `false` | 允许某组合失败不阻断 |
| `max-parallel` | 矩阵 | 无限制 | 保护共享 DB/配额 |

## 13.3 在工作流中使用容器 (Using Containers in Your Workflow)

* **核心主旨**：利用 Docker 容器技术封装独立的运行环境、工具链或后台服务，确保工作流在绝对一致的隔离空间内执行。
* **三种核心容器应用模式**：

| 模式 | 关键字 | 作用范围 |
|------|--------|----------|
| 作业运行环境 | `container:` | 该 job 所有 steps |
| 单步容器 | `uses: docker://...` | 当前 step |
| 后台服务 | `services:` | job 级 sidecar（DB/缓存） |

1. **将容器作为作业的运行环境 (Using a Container as the Environment for a Job)**：
   * **语法要点**：在作业层级使用 **`container:`** 关键字（支持属性包含 `image`, `credentials`, `env`, `ports`, `options`）。
   * **逻辑脉络**：一旦指定，该作业下的**所有**步骤（`steps`）都会在此 Docker 容器内部执行，而非在底层的 Runner 虚拟机上执行。常用于拉取包含特定构建工具集的自定义镜像。

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: golang:1.22
    steps:
      - uses: actions/checkout@v4
      - run: go build ./...
```

2. **在单个步骤中使用容器 (Using a Container with a Step)**：
   * **实现机制**：实际上是调用 **Docker 容器操作 (Docker Container Actions)**。通过 `uses: docker://<镜像路径>` 语法，仅针对当前特定步骤实例化并运行一个容器。

```yaml
- uses: docker://alpine:3.19
  with:
    args: echo "hello from alpine"
```

3. **将容器作为后台服务运行 (Running Containers as Services in a Job)**：
   * **关键定义**：在作业层级使用 **`services:`** 关键字配置后台守护进程（如 MySQL、Redis 等数据库或缓存服务）。
   * **交互逻辑**：服务容器会在作业主步骤开始前启动，主作业步骤可以通过指定的网络端口（如 `127.0.0.1:3306`）访问这些服务容器，用于执行集成测试或数据初始化。可以配合 `options: --health-cmd` 设置健康检查以确保服务可用后再执行主代码。

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: testdb
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - run: go test ./... -tags=integration
        env:
          DATABASE_URL: mysql://root:root@127.0.0.1:3306/testdb
```

## 13.4 结论 (Conclusion)

* **重点结论**：
  * 本章通过三种高级范式彻底拓展了工作流的边界：通过 **CLI/API** 赋予了工作流直接操控平台生态的能力；通过**矩阵策略**实现了跨维度组合的高阶动态并发；通过**容器化集成**确保了异构环境的一致性与服务的无缝拉起。
* **知识点关联与逻辑过渡**：
  * 掌握了包含矩阵和容器在内的全套 Actions 高级编排技术后，现有的 GitHub 内置 CI/CD 能力已足够支撑任何复杂的企业级架构。这也为本书最后一章（第14章：讲解如何从传统的 Jenkins、GitLab CI 等外部平台无缝**迁移**至 GitHub Actions）提供了完整的技术理论储备。
