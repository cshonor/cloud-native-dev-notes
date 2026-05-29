# 第14章：迁移到 GitHub Actions (Migrating to GitHub Actions)

> **后端学习提示**：本章**跳过**。属企业级平台迁移场景；个人/小团队从零用 Actions 即可，无需学 Importer。了解 **14.2 各平台概念映射** 有助于读懂旧项目 CI 配置。

## 14.1 准备工作 (Prep)

* **核心主旨**：在将现有的 CI/CD 工作流从其他平台迁移至 GitHub Actions 之前，必须对代码库、自动化脚本、基础设施以及团队用户进行全面的评估与规划。
* **核心知识点与逻辑脉络**：
  * **源代码 (Source Code)**：Actions 和工作流直接绑定在 GitHub 存储库中，因此必须先将代码迁移至 GitHub。**关键考量点**：是迁移所有项目还是部分项目？保留全部提交历史还是仅迁移最新代码？需要迁移哪些分支？是否需要进行数据清理？
  * **自动化 (Automation)**：需要审查现有的自动化构建定义文件和自定义脚本，评估其在 GitHub Actions 框架下的兼容性与迁移成本。
  * **基础设施 (Infrastructure)**：审查自定义的配置和依赖项。**因果推演**：如果目前的作业依赖于必须在构建前后持续可用的物理机，那么迁移到每次运行完即销毁的短暂性 (Ephemeral) 虚拟机上是否可行？如果当前使用的是 macOS 或 Windows 节点，是否可以切换为 Linux 环境以大幅降低资源成本？
  * **用户 (Users)**：评估迁移对团队成员的影响，明确需要进行哪些培训或引导以帮助他们适应新平台。
* **预留拓展补充空间**：
  * *【拓展建议】：在企业级落地时，可补充如何制定详细的分阶段迁移时间表（例如：先迁移测试项目，再迁移非核心业务，最后迁移核心生产流），以将业务中断的风险降至最低。*

```
迁移评估清单
├── 代码：仓库数量、分支策略、历史是否保留
├── 自动化：Jenkinsfile / .gitlab-ci.yml 等 → Actions YAML
├── 基础设施：自托管节点 → GitHub-hosted？Secrets 如何迁移？
└── 人员：培训、并行运行期、回滚方案
```

## 14.2 从各大主流 CI/CD 平台迁移的核心差异点

* **核心主旨**：不同的 CI/CD 工具在语法结构、组件层级和执行模型上存在差异，迁移的核心在于理解这些底层概念到 GitHub Actions 的映射关系。
* **各平台关键差异对比 (案例数据与公式要点)**：

| 概念 | Azure Pipelines | CircleCI | GitLab CI | Jenkins | Travis CI | **GitHub Actions** |
|------|-----------------|----------|-----------|---------|-----------|-------------------|
| 运行环境 | `vmImage` | `docker` / executor | 顶层 `image` | `agent` | `os` | `runs-on` / `container:` |
| 阶段/作业 | `stages` + `jobs` | `workflows` | `stages` + `jobs` | `stages` | `phases` | `jobs` |
| 步骤 | `steps` | `steps` | `script` | `steps` | `script` | `steps` |
| 多工作流文件 | 单文件多 stage | `config.yml` 多 workflow | 单 `.gitlab-ci.yml` | Jenkinsfile | `.travis.yml` | **每工作流独立 YAML** |
| 矩阵 | `strategy.matrix` | 自定义分组 | `parallel:matrix` | 插件 | `matrix: include` | `strategy.matrix` |
| 分支过滤 | `trigger: branches` | `filters` | `only/except` | 插件配置 | `branches: only` | `on.push.branches` |

* **Azure Pipelines**：在 Azure 中通过 `vmImage` 指定运行环境，而在 Actions 中使用 `runs-on`；Azure 支持将多个阶段 (stages) 的工作流组合在同一个文件中，而 Actions 强制要求每个独立的工作流必须使用单独的 YAML 文件。
* **CircleCI**：CircleCI 可以在 `config.yml` 中声明一个 `group` 来组合多个工作流，Actions 则没有此分组概念，均独立为 YAML 文件；在处理测试并发时，CircleCI 根据自定义规则或历史时间分组，而 Actions 则使用**矩阵策略 (Matrix strategy)**。
* **GitLab CI/CD**：GitLab 在顶层声明 `image` 以指定全局 Docker 镜像，Actions 则在具体的作业层级使用 `container:` 语法。
* **Jenkins**：Jenkins 使用**声明式管道 (Declarative pipelines)**，Actions 使用 YAML 规范；Jenkins 使用 `agent` 分配节点，Actions 使用 `runner`；Jenkins 将步骤组合为 `stages`，Actions 将步骤组合为 `jobs`。
* **Travis CI**：Travis CI 使用 `phases` 进行阶段划分，Actions 使用 `jobs`；在指定分支触发规则时，Travis CI 语法为 `branches: only:`，Actions 语法为 `on: push: branches:`；对于矩阵构建，Travis CI 使用 `matrix: include`，Actions 使用 `jobs: <job_id>: strategy: matrix:`。

```yaml
# Jenkins declarative → Actions 概念映射
# agent { label 'linux' }     →  runs-on: ubuntu-latest
# stages { stage('Build') }   →  jobs.build
# steps { sh 'make' }         →  steps: - run: make
```

## 14.3 GitHub Actions Importer 自动化迁移工具 ⏭️ 后端跳过

* **核心主旨**：面对数百乃至数千个工作流的庞大迁移工程，手动重写代码并不现实，GitHub 官方提供了 `GitHub Actions Importer` 工具，用于自动化转换外部 CI/CD 管道代码。
* **核心定义与基础设置**：
  * **GitHub Actions Importer**：作为 GitHub CLI (`gh`) 的一个扩展插件运行。安装命令为 `gh extension install github/gh-actions-importer`。
  * **身份验证 (Authentication)**：通过运行 `gh actions-importer configure`，启动交互式提示，配置源 CI 服务器（如 Jenkins）的访问凭据和目标 GitHub Personal Access Token。
* **逻辑脉络与核心工作流 (命令解析)**：

| 阶段 | 命令 | 作用 |
|------|------|------|
| 审计 | `audit` | 评估可转换比例，按步骤粒度列兼容/不兼容项 |
| 预测 | `forecast` | 基于历史运行数据估算 Runner 数量与成本 |
| 试运行 | `dry-run` | 本地预览转换结果，不提交代码 |
| 自定义 | `--custom-transformers` | Ruby 规则映射特殊插件/语法 |
| 执行 | `migrate` | 转换并在目标仓库自动开 PR |

1. **审计 (Audit)**：使用 `audit` 命令分析当前 CI/CD 的整体规模。该操作会生成总结报告，按照完全成功 (Successful)、部分成功 (Partially successful)、不支持 (Unsupported) 和失败 (Failed) 的指标，精准呈现可以自动化转换的比例。报告还会细化到**构建步骤 (Build steps)** 层级，列出哪些插件或脚本指令已知可以直接转换，哪些是未知或不兼容的。
2. **预测 (Forecasting)**：使用 `forecast` 命令分析目标平台过去一段时间内的历史运行数据（如排队时间、执行时间、并发作业数）。**实用结论**：利用预测产出的"执行时间"和"并发作业数"指标，企业可以精确估算迁移至 GitHub Actions 后所需的运行器 (Runner) 数量与计算成本。
3. **试运行 (Doing a Dry Run)**：使用 `dry-run` 命令在本地模拟转换单条管道。它将输出转换后的 YAML 文件以及由于兼容性无法自动转换的错误日志，供开发者提前预览转换效果而不提交任何代码。
4. **自定义转换器 (Custom Transformers)**：当遇到源 CI 平台中自定义的插件或特殊构建逻辑时（例如 Jenkins 的特定休眠指令或文件写入构造），系统默认无法转换。**公式要点**：开发者可以使用 **Ruby** 语言编写自定义映射规则 (Transformers)，告诉导入器如何将特定的外部语法翻译为等效的 GitHub Actions 步骤。随后在运行命令时通过 `--custom-transformers` 参数引入该规则文件。
5. **执行迁移 (Doing the Actual Migration)**：使用 `migrate` 命令拉取源代码，自动转换为 Actions YAML 格式，并**直接在目标 GitHub 存储库中自动创建一个 Pull Request**。

```bash
# 安装与配置
gh extension install github/gh-actions-importer
gh actions-importer configure

# 典型流程
gh actions-importer audit jenkins --output-dir ./audit
gh actions-importer dry-run jenkins --source-file Jenkinsfile --output-dir ./out
gh actions-importer migrate jenkins --output-dir ./migrate
```

* **易错细节与后续收尾 (Manual Tasks)**：
  * **自动迁移的盲区**：导入器无法自动迁移平台内存储的**机密数据 (Secrets)**、非标准的自托管运行器标签以及包管理配置 (Packages)。
  * 在最终生成的 Pull Request 中，系统会智能追加一段名为 **"Manual steps (手动步骤)"** 的清单，明确列出开发者必须在 GitHub UI 中手动补齐的配置（例如："请确保在仓库设置中添加名为 `BUILD_ADMIN_USER_PASS` 的 Secret"），当这些手动事项与代码审查均完成后，方可合并 Pull Request 实现闭环。
* **预留拓展补充空间**：
  * *【拓展方向】：可补充如何利用 IssueOps 模式（在 GitHub Issue 中通过特定指令触发迁移），实现跨部门大规模迁移过程中的自助式 (Self-Service) 转换服务。*

## 14.4 结论 (Conclusion)

* **重点结论**：GitHub 原生支持与多种外部自动化平台集成，但借助 GitHub Actions，用户可以直接将自动化流转能力深植于 GitHub 内部，享受最紧密的生态协同体验。
* **前后因果关系**：本章总结了使用自动化导入工具降低企业级迁移门槛的整体链路。从最初评估代码库状态，到使用 `audit` 进行可行性分析，再通过 `dry-run` 和自定义 `Transformers` 处理特殊语法，最终通过自动生成的 Pull Request 完成平滑过渡，为全书的 GitHub Actions 自动化实践画上了一个完整的句号。
