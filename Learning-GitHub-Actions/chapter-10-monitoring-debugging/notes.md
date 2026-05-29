# 第10章：监控、日志与调试 (Monitoring, Logging, and Debugging)

> **后端学习提示**：本章**必学**。掌握 Actions 界面排查、Re-run 失败作业、`ACTIONS_STEP_DEBUG` 和 Workflow Commands 即可应对日常流水线故障。

## 10.1 获得更多可观察性 (Gaining More Observability)

* **核心主旨**：利用 GitHub Actions 内置的可视化工具和过滤机制，在宏观层面上追踪工作流的执行状态并向外部展示。
* **核心知识点与关键定义**：
  * **宏观状态追踪**：通过存储库的 `Actions` 选项卡，可以查看所有工作流运行的连续历史记录。每条记录都会显示触发事件、状态、分支和触发者信息。
  * **搜索与过滤查询 (Filtering by Query)**：支持在搜索框中使用键值对进行精确搜索（如 `is:failure`、`event:push`、`workflow:name`）或通过下拉菜单按事件、状态、分支进行快速过滤。
  * **状态徽章 (Status Badges)**：一种 Markdown 格式的可视化指示器（显示通过 passing / 失败 failing），通常嵌入在 `README.md` 文件中，点击后可直接跳转至对应的工作流运行列表。
* **逻辑脉络与实用要点**：
  * 可观察性的建立是一个从**全局监控**（查看全部运行记录）到**单点聚焦**（点击特定工作流查看详细运行）的过程。
  * **状态徽章生成逻辑**：在 Actions 界面可通过「Create status badge」对话框自动生成针对特定分支和事件的 Markdown 源码。徽章不仅是展示工具，更是连接项目首页与底层 CI/CD 状态的桥梁。
* **拓展建议**：
  * 可通过 GitHub API 自动抓取徽章状态，用于构建企业内部的集中式 CI/CD 监控大盘。

```markdown
![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg?branch=main)
```

```
# 常用过滤查询
is:failure
event:push
workflow:CI
branch:main
```

## 10.2 使用历史状态 (Working with Past States)

* **核心主旨**：不仅提供静态日志浏览，还允许开发者将时间回溯至最初触发时的上下文，并通过重新运行机制排查偶发性故障。
* **关键定义与核心机制**：
  * **映射工作流版本 (Mapping Workflow Versions)**：系统会记录工作流运行瞬间的 YAML 文件快照。通过「View workflow file」功能，可以直接跳转至该次运行所对应的具体 **Git 提交哈希 (Commit SHA)** 状态，防止代码变更干扰排查。
  * **30 天重跑窗口期**：在工作流最初运行的 **30 天**内，GitHub 允许对工作流进行重新运行 (Re-run)。
* **因果流与重跑策略 (Re-running Strategies)**：
  * **重新运行所有作业 (Re-run all jobs)**：重新执行整个管道。
  * **仅重新运行失败的作业 (Re-run failed jobs)**：仅重跑失败节点及其**下游依赖作业 (dependent jobs)**。此模式在修复了短暂的环境问题（如网络抖动）后极为高效。
  * **单节点重跑**：悬停在特定作业上，可点击圆形箭头图标仅重跑该单个作业及其依赖项。
* **易错细节与重点结论**：
  * **状态继承**：当重新运行单个或失败作业时，任何之前成功运行的作业所生成的**输出 (outputs)**、**制品 (artifacts)** 及其绑定的**环境前置保护规则 (environment protection rules)** 将被自动继承和复用。
  * **多运行实例追踪**：重跑后，系统会保留历史记录，并在界面顶部提供一个下拉菜单（如 `Attempt #1`、`Latest attempt #2`）以对比不同次重跑的结果差异。

## 10.3 调试工作流 (Debugging Workflows)

* **核心主旨**：当标准日志不足以诊断问题时，通过激活底层诊断日志，获取系统变量、事件求值与运行器通信的深度细节。
* **核心知识点（双重调试模式）**：
  * **步骤调试日志 (Step Debug Logging)**：
    * **触发条件**：将机密 (Secret) 或变量 (Variable) **`ACTIONS_STEP_DEBUG`** 设置为 `true`。
    * **行为**：使 GitHub Actions 引擎在 UI 日志中输出极高密度的信息，包含表达式求值结果、上下文输出等，信息以 `##[debug]` 为前缀且高亮显示。
  * **运行器诊断日志 (Runner Diagnostic Logging)**：
    * **触发条件**：将 **`ACTIONS_RUNNER_DEBUG`** 设置为 `true`。
    * **行为**：记录运行器与 GitHub 控制平面的底层交互及作业分发的通信细节。
* **案例数据与易错细节**：
  * **视图盲区**：运行器诊断日志**无法**在浏览器 UI 中直接查看。必须点击「Download log archive」下载压缩包，解压后在 `runner-diagnostic-logs` 文件夹内查看以 `Runner_` 和 `Worker_` 开头的原始文本文件。
  * **快捷激活逻辑**：在触发重新运行 (Re-run) 操作时，确认对话框底部提供了一个 **「Enable debug logging」** 复选框。勾选此项可以在不修改全局 Secret 的情况下，仅对该次重跑**临时强制开启**步骤调试日志。

| Secret / Variable | 作用 | 查看位置 |
|-------------------|------|----------|
| `ACTIONS_STEP_DEBUG=true` | 表达式求值、上下文详情 | Actions UI 日志 |
| `ACTIONS_RUNNER_DEBUG=true` | Runner 与控制面通信 | 下载 log archive |

## 10.4 增强与自定义日志记录 (Augmenting and Customizing Logging)

* **核心主旨**：开发者可利用特殊的 Workflow 命令 (echo 指令) 拦截日志流，注入自定义结构、脱敏敏感信息，甚至生成富文本的摘要报告。
* **公式要点与工作流命令 (Workflow Commands) 语法**：
  * **输出各类通知**：
    * 警告：`echo "::warning::[message]"`
    * 提示：`echo "::notice::[message]"`
    * 错误：`echo "::error::[message]"`
    * 可附加元数据定位到具体代码行：`::error file=app.js,line=10,col=15::Something went wrong`。这些消息会自动汇总到作业的 Annotations（注解）面板中。
  * **日志折叠 (Log Grouping)**：
    * 开始：`echo "::group::[GroupTitle]"`
    * 结束：`echo "::endgroup::"`。用于将冗长的安装或编译日志折叠收纳，提升可读性。
  * **手动脱敏掩码 (Masking Values)**：
    * 语法：`echo "::add-mask::$VARIABLE_NAME"`。
    * 逻辑：强制引擎在后续打印该变量值时，将其替换为 `***`。这不仅适用于普通字符串，也可用于脱敏非敏感的**配置变量 (vars)**。
* **实用要点：自定义作业摘要 (Customized Job Summary)**：
  * **概念**：除了钻取底层日志，开发者可通过向特殊的全局环境文件 **`$GITHUB_STEP_SUMMARY`** 追加 Markdown 文本，动态生成当前作业的宏观战报。
  * **排版能力**：完全支持 GitHub 风格的 Markdown，包括表格、表情符号 (Emojis) 等。

```yaml
- name: Build with grouped logs
  run: |
    echo "::group::Install dependencies"
    npm ci
    echo "::endgroup::"
    echo "::notice::Build completed successfully"

- name: Job summary
  run: |
    echo "## Test Results" >> $GITHUB_STEP_SUMMARY
    echo "| Test | Result |" >> $GITHUB_STEP_SUMMARY
    echo "|------|--------|" >> $GITHUB_STEP_SUMMARY
    echo "| unit | ✅ pass |" >> $GITHUB_STEP_SUMMARY
```

## 10.5 结论 (Conclusion)

* **重点结论**：
  * GitHub Actions 建立了一套多层次的可观测体系：从外层的**状态徽章**，到列表级的**多维度过滤器**，再到可时间回溯的**重新运行机制**，最终深入到底层的**双重调试日志**。
  * 开发者并非只能被动接收日志，通过 **Workflow Commands** 和 **Job Summaries**，系统赋予了开发者主动改造日志展现形态与屏蔽敏感数据的能力。
* **知识点关联逻辑**：
  * 掌握了故障排查、安全监控（第九章）与日志追踪技术后，保障了企业级 CI/CD 自动化运行的稳健性。这为进阶探索如何抽象与复用这些自动化逻辑——即创建**自定义操作 (Custom Actions)**（第十一章）奠定了运维层面的基础。

## 本章速记（后端必记）

| 场景 | 操作 |
|------|------|
| 查失败原因 | Actions → 运行记录 → Job → Step 日志 |
| 偶发失败重试 | Re-run failed jobs |
| 表达式/debug | 设 `ACTIONS_STEP_DEBUG=true` 或 Re-run 勾选 debug |
| 折叠冗长日志 | `::group::` / `::endgroup::` |
| 生成测试报告 | 写入 `$GITHUB_STEP_SUMMARY` |
| 查看当时 YAML | View workflow file（对应 Commit SHA） |
