# 第11章：创建自定义操作 (Creating Custom Actions)

> **后端学习提示**：本章**选学**。重点掌握 `action.yml` 结构、**Composite** 与**本地 Action**（`.github/actions/`）；Docker/JS Action 与 Marketplace 发布属进阶，日常用公开 Action 即可。

## 11.1 操作的剖析 (Anatomy of an action)

* **核心主旨**：自定义操作 (Custom Actions) 的底层代码形式极具弹性，可以是简单的 Shell 脚本，也可以是包含复杂逻辑和独立 CI/CD 流水线的代码库。其核心通过元数据文件进行规范化配置。
* **核心知识点与关键定义**：
  * **`action.yml`**：定义操作的输入 (inputs)、输出 (outputs) 和环境配置的核心元数据文件。
  * **Inputs（输入参数属性）**：包含 `input_id`（唯一标识符，仅限字母数字或中划线/下划线）、`description`（描述）、`required`（是否必填）、`default`（默认值）以及 `deprecationMessage`（弃用警告信息）。
  * **Outputs（输出参数属性）**：包含 `output_id` 和 `description`。对于复合操作 (Composite) 或 JS 操作，还需指定与环境输出绑定的 `value` 值。
  * **Branding（品牌化标识）**：可在 `action.yml` 中使用 `branding` 块定义在操作市场展示的 `icon`（图标，来源于 feathericons）和 `color`（颜色）。
* **逻辑脉络与实用要点**：
  * 在工作流中通过 `with` 子句传递的值必须与 `action.yml` 中定义的 `input_id` 严格映射；同样，获取结果时需通过预设的 `output_id` 提取。

```yaml
# action.yml 骨架
name: 'My Action'
description: '示例自定义操作'
inputs:
  greeting:
    description: '问候语'
    required: true
    default: 'Hello'
outputs:
  message:
    description: '拼接后的消息'
runs:
  using: 'composite'
  steps: []
branding:
  icon: 'zap'
  color: 'blue'
```

```yaml
# 工作流中调用
- uses: ./.github/actions/my-action
  id: greet
  with:
    greeting: 'Hi'
- run: echo "${{ steps.greet.outputs.message }}"
```

## 11.2 操作的类型 (Types of Actions)

* **核心主旨**：GitHub 提供了三种主要的自定义操作构建模式，分别适用于不同的运行环境要求和性能开销约束。
* **核心分类与逻辑脉络**：

| 类型 | `runs.using` | 运行环境 | 后端常用 |
|------|--------------|----------|----------|
| Composite | `composite` | 当前 Runner 宿主机 | ✅ 封装重复 steps |
| Docker | `docker` | Linux 容器 | 需强环境隔离时 |
| JavaScript | `node20` 等 | Node.js 运行时 | 复杂逻辑、Toolkit |

1. **复合操作 (Composite Action)**：
   * **语法要点**：在 `action.yml` 中设定 `runs: using: "composite"`。
   * **执行逻辑**：允许将多个原生步骤（如同在工作流 job 中写 steps 一样）封装为一个独立操作，直接在当前的运行器环境中按顺序执行 Shell 脚本或外部命令。
   * **数据返回**：通过重定向写入 `${{ github.action_path }}` 执行脚本的结果至 **`$GITHUB_OUTPUT`** 来实现输出值绑定。

```yaml
# .github/actions/setup-go/action.yml
name: 'Setup Go'
description: '安装 Go 并输出版本'
inputs:
  go-version:
    description: 'Go 版本'
    required: false
    default: '1.22'
outputs:
  version:
    description: '实际安装的版本'
    value: ${{ steps.detect.outputs.version }}
runs:
  using: 'composite'
  steps:
    - shell: bash
      run: |
        go version
        echo "version=$(go version | awk '{print $3}')" >> "$GITHUB_OUTPUT"
      id: detect
```

2. **Docker 容器操作 (Docker Container Action)**：
   * **语法要点**：设定 `runs: using: 'docker'`。
   * **执行逻辑与限制**：强制代码在指定的 Linux 容器内运行，确保环境绝对一致性。可以通过 `image: 'docker://<镜像地址>'` 直接引用预构建的远程镜像，以节省每次运行时的镜像构建开销。
   * **易错细节**：在 Dockerfile 中**禁止使用 `USER` 指令**（必须默认为 root）。如果通过 `ENTRYPOINT` 传入环境变量，注意 exec 形式（如 `["/entrypoint.sh"]`）不会自动进行环境变量的宏求值。

```yaml
runs:
  using: 'docker'
  image: 'docker://ghcr.io/owner/my-action:1.0.0'
  # 或 image: 'Dockerfile'  每次运行构建
```

3. **JavaScript 操作 (JavaScript Action)**：
   * 利用原生的 Node.js 运行时执行。通常借助 Actions Toolkit 的 `core` 模块（如 `core.getInput`, `core.setOutput`, `core.setFailed`）实现更高级的数据交互与系统状态拦截。

```javascript
const core = require('@actions/core');
const input = core.getInput('name', { required: true });
core.setOutput('greeting', `Hello, ${input}`);
```

## 11.3 完成您的操作创建 (Completing Your Action Creation)

* **核心主旨**：规范化地为操作打上版本标签，以便调用方在使用时能锁定正确的依赖版本。
* **实用要点与版本控制策略**：
  * **调用语法**：`uses: creator/action-name@v#`。
  * **最佳实践**：通常建议用户仅绑定到**主版本号标签 (Major version tag)**，例如 `@v2`。这样既能自动获得向后兼容的次要更新与补丁修复，又能避免因重大破坏性更新而导致流水线中断。

```
v1.0.0  →  打 tag v1.0.0，并移动 major 指针 v1
v1.0.1  →  补丁修复，仍用 @v1 调用
v2.0.0  →  破坏性变更，调用方需显式升级到 @v2
```

## 11.4 在 GitHub Marketplace 上发布操作 (Publishing Actions on the GitHub Marketplace) ⏭️ 后端跳过

* **核心主旨**：将本地存储库转化为开源生态共享组件的完整提交流程与规范要求。
* **格式硬性规则与发布前置条件**：
  * 操作必须存放于**公开存储库 (Public repository)**，且根目录下必须存在 `action.yml`（或 `.yaml`）。
  * 存储库名称必须全局唯一，不可与现有分类同名，且禁用 GitHub 官方保留字。
  * 必须在页面上明确包含 `README.md` 文件以说明使用方式。
* **逻辑脉络（发布工作流）**：
  * 进入存储库页面的 "Draft a release" → 遵循**语义化版本控制 (Semantic versioning, 如 v1.0.0)** 创建标签 → 勾选并接受 GitHub Marketplace 开发者协议 → 填充分类并发布。
* **预留拓展补充空间**：
  * *【拓展建议】：发布后，若该 Action 被提交了 Pull Request 以更新 README 或功能，所有合并至默认分支的变更将自动同步映射到操作市场页面，这涉及开源代码维护者的标准协作流。*

## 11.5 Actions 工具包 (The Actions Toolkit)

* **核心主旨**：为不使用 JavaScript 编写自定义 Action 的用户，提供一套基于特定语法拦截规则的"工作流命令 (Workflow Commands)"，实现与 Toolkit API 等效的底层环境控制力。
* **公式要点与命令映射表**：

| Toolkit API | 工作流命令（Shell 等效） |
|-------------|--------------------------|
| `core.addPath` | `echo "/path" >> $GITHUB_PATH` |
| `core.exportVariable` | `echo "KEY=val" >> $GITHUB_ENV` |
| `core.setOutput` | `echo "key=val" >> $GITHUB_OUTPUT` |
| `core.setFailed` | `echo "::error::msg"` + `exit 1` |
| 行内注解 | `echo "::error file=app.js,line=10::Missing key"` |

* **易错细节（命令解析陷阱）**：
  * **单行限制与转义**：工作流命令必须写在**物理单行**上。如果注入的内容中包含特殊字符，必须进行严格的 **URL 编码 (URL encoded)**。
  * **关键转义映射**：`%` 需转换为 `%25`；换行符 `\n` 需转换为 `%0A`；回车符 `\r` 需转换为 `%0D`。

```bash
# 带文件定位的错误注解
echo "::error file=src/main.go,line=42::undefined variable"

# 多行输出需 URL 编码
echo "summary<<EOF" >> $GITHUB_OUTPUT
echo "line1" >> $GITHUB_OUTPUT
echo "EOF" >> $GITHUB_OUTPUT
```

## 11.6 本地操作 (Local actions)

* **核心主旨**：当某个自定义脚本仅在单一项目内具有复用价值时，无需为其建立独立的公开存储库，可直接在项目内部构造"本地操作"。
* **格式硬性规则与路径规范**：
  * **存放位置**：本地操作的代码和 `action.yml` 必须存放在当前存储库特定的子目录中，标准做法是保存在 **`.github/actions/<action-name>/`** 路径下。
* **调用语法与逻辑关联**：
  * 在同一存储库的正常工作流中，使用**相对路径**调用该操作：`uses: ./.github/actions/<action-name>`。这种模式允许极其轻量级地封装重复代码，同时完美继承所在存储库的安全边界。

```
.github/
├── workflows/
│   └── ci.yml
└── actions/
    └── lint-go/
        └── action.yml
```

```yaml
# .github/workflows/ci.yml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/lint-go
        with:
          version: '1.22'
```
