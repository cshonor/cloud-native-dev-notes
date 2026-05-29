# 第6章：管理您的工作流环境 (Managing Your Workflow Environments)

## 6.1 命名工作流与工作流运行 (Naming Your Workflow and Workflow Runs)

* **核心主旨**：通过语法关键字为自动化工作流设定可读名称，以便于在可视化界面中进行识别与管理。
* **核心知识点与关键定义**：
  * 在工作流文件的顶部使用 `name` 关键字，可以设置该工作流在 GitHub Actions 选项卡中显示的**展示名称**。
* **逻辑脉络与段落分层**：
  * **命名需求**：在复杂的 CI/CD 自动化过程中，准确标识工作流是第一步。
  * **层级结构**：`name` 字段位于 YAML 文件的顶层，独立于触发器和作业定义。
* **拓展补充**：
  * 使用 `run-name` 可基于动态上下文（如分支、提交信息）命名单次**工作流运行 (Workflow Run)**：

```yaml
name: CI Pipeline
run-name: ${{ github.actor }} pushed to ${{ github.ref }}
```

## 6.2 上下文 (Contexts)

* **核心主旨**：上下文提供了一种在工作流运行期间动态读取和访问环境、作业、步骤及触发事件数据的机制。
* **关键定义与核心上下文分类**：
  * **Contexts（上下文）** 是一系列对象，包含了与执行相关的动态属性。
  * **`github`**：包含工作流运行及其触发事件的数据属性（如 `github.repository`、`github.ref` 等）。
  * **`env`**：访问在工作流、作业或步骤级别设置的环境变量。
  * **`vars`**：访问存储库、环境或组织级别的非敏感配置变量。
  * **`secrets`**：访问加密机密数据（如 `secrets.GITHUB_TOKEN`）。
  * **`strategy` / `matrix`**：在矩阵执行期间，访问当前作业对应的矩阵变量和策略信息。
  * **`needs`**：用于收集和访问已定义依赖关系的前置作业的输出（如 `needs.<job_id>.outputs`）。
  * **`inputs`**：访问传递给可重用工作流或手动触发工作流的输入属性。
* **公式要点与语法规范**：
  * **数据引用**：通过标准表达式语法 `${{ context.property }}` 提取变量值。
  * **条件评估**：常用于 `if` 条件语句控制执行流，例如 `if: github.ref == 'refs/heads/main'`。
* **易错细节**：
  * 某些上下文属性仅在特定触发事件中存在（例如 `github.head_ref` 仅在 Pull Request 中定义），在不受支持的事件中调用会导致意外的语法错误。

## 6.3 环境变量 (Environment Variables)

* **核心主旨**：定义自定义环境配置，控制数据在不同运行层级的覆盖和继承关系。
* **核心知识点**：
  * 通过定义 **`env` 块**（变量到值的映射）来创建**自定义环境变量 (custom environment variables)**。
  * 环境变量同样支持上下文动态求值，例如 `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`。
* **逻辑脉络与作用域覆盖规则**：
  * **作用域定义**：可在三个层级定义：**工作流级别 (Workflow level)**、**作业级别 (Job level)**、**步骤级别 (Step level)**。
  * **层级优先级（因果覆盖逻辑）**：如果在多个层级存在同名变量，**步骤级别**覆盖作业和工作流级别；**作业级别**覆盖工作流级别。
  * **默认执行设置 (`defaults`)**：同理，可通过 `defaults` 块统一设置执行器行为（如 `run: shell: bash`），其优先级逻辑与环境变量完全一致。

## 6.4 机密与配置变量 (Secrets and Configuration Variables)

* **核心主旨**：安全且可重用地管理跨越多个工作流的敏感与非敏感级数据。
* **关键定义**：
  * **Secrets（机密）**：用于存储必须隐藏或加密的敏感数据。
  * **Configuration Variables（配置变量）**：用于存储非敏感的共享参数。
* **逻辑脉络与作用域配置**：
  * 可在**存储库 (Repository)**、**组织 (Organization)** 或 **部署环境 (Environment)** 这三个维度进行设置。
  * **优先级顺序**：当出现同名数据时，**部署环境 > 存储库 > 组织**。
* **实用要点与配置要求**：
  * **命名规范**：必须唯一，仅包含字母数字或下划线，不可包含空格，不可数字开头，**禁用 `GITHUB_` 前缀**，不区分大小写。
  * **组织级变量分发**：支持精细控制变量对哪些存储库可见（所有公开存储库、所有私有存储库或特定选择的存储库）。

## 6.5 管理工作流权限 (Managing Permissions for Your Workflow)

* **核心主旨**：通过声明式语法对内置访问令牌应用「最小权限原则」，控制系统资源读写边界。
* **关键定义与权限范围**：
  * **`GITHUB_TOKEN`**：GitHub 自动向作业注入的内置认证令牌。
  * **默认行为**：工作流配置可设为**宽松权限 (Permissive, 默认为 read/write)** 或 **受限权限 (Restricted, 默认为 read-only 或 none)**。包含的作用域如 `contents`、`issues`、`pull-requests`、`packages` 等。
* **实用要点与语法要点**：
  * 通过 **`permissions`** 关键字精准赋予所需权限，例如 `permissions: issues: write`。
* **易错细节与安全边界**：
  * **一旦在工作流中显式使用了 `permissions` 关键字指定某项权限，所有未提及的作用域将自动隐式降级为 `none`**（必须明确声明所有需要的读写流）。
  * 在 Fork 存储库的 Pull Request 环境中，默认具有限制性质，即使明确要求写入权限也可能受阻，以防止未经授权的代码篡改。

## 6.6 部署环境 (Deployment Environments)

* **核心主旨**：通过逻辑环境的隔离，为自动化部署施加前置安全检查与专有变量绑定。
* **关键定义**：
  * **Environments（环境）**：在 GitHub 中创建的逻辑对象，用于标识部署的总体目标（如 `dev`、`test`、`production`）。
* **逻辑脉络与核心特性**：
  * **作业绑定**：在作业定义中使用 `environment:` 子句将当前作业显式绑定到目标环境。
  * **访问控制（因果触发）**：一旦绑定，作业将强制遵循环境级别的**部署保护规则 (Deployment protection rules)**（例如：必须等待特定人员的审核批准，或必须等待设置的计时器时间）。
  * **数据隔离**：作业只有在被授权部署到特定环境时，才能访问该环境独有的环境级 `secrets` 和 `vars`（例如生产环境的 `PROD_TOKEN`）。
* **拓展方向**：
  * 配置基于特定分支（如仅允许 `main` 分支）才能触发特定环境的部署，避免测试分支意外污染生产环境。

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
    environment: production
    runs-on: ubuntu-latest
    steps:
      - run: echo "deploy to prod"
```
