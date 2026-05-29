# 第7章：在工作流中管理数据 (Managing Data Within Workflows)

## 7.1 在工作流中使用输入和输出 (Working with Inputs and Outputs in Workflows)

* **核心主旨**：在分布式的自动化阶段（步骤间、作业间、工作流间）传递和共享状态及执行结果。
* **核心知识点与逻辑脉络**：
  1. **管理输入 (Inputs)**：通过 `workflow_call`（可重用工作流）或 `workflow_dispatch`（手动触发）捕获用户或进程显式提供的参数，并通过 `${{ inputs.<input-name> }}` 获取。
  2. **捕获步骤输出 (Step Outputs)**：需给产生输出的步骤设置 `id:`。在步骤内将键值对追加到专用的环境变量文件 `$GITHUB_OUTPUT` 中。提取路径为 `steps.<step_id>.outputs.<output_name>`。
  3. **捕获作业输出 (Job Outputs)**：跨作业数据传递必须在源作业中定义 `outputs:` 块，将步骤的输出映射为作业级输出。随后在目标作业中声明 `needs: <源作业id>`，并通过 `${{ needs.<job_id>.outputs.<output_name> }}` 进行提取。
  4. **捕获外部 Action 输出**：在 `action.yml` 中定义的返回值，同样以步骤 `id` 作为挂载点进行读取。
* **易错细节**：
  * **语法弃用警告**：早期使用的特殊命令 `echo "::set-output name={name}::{value}"` 已经被视为存在注入风险并被**弃用**，现代规范必须使用写入 `$GITHUB_OUTPUT` 的形式：`echo "{name}={value}" >> $GITHUB_OUTPUT`。
  * **信任边界**：从触发上下文或用户输入获取的数据属于**不可信数据 (Untrusted Input)**，需警惕 Shell 脚本注入风险。

```yaml
# 步骤输出示例
- id: meta
  run: echo "version=1.0.0" >> $GITHUB_OUTPUT

# 作业输出示例
jobs:
  build:
    outputs:
      version: ${{ steps.meta.outputs.version }}
    steps:
      - id: meta
        run: echo "version=1.0.0" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.version }}"
```

## 7.2 定义制品 (Defining Artifacts)

* **关键定义**：
  * **Artifacts（制品）**：工作流执行期间生成并上传到 GitHub 的文件或集合（如编译的二进制文件、测试报告等），用于持久化数据并在后续作业中共享。
* **案例数据与生命周期策略**：
  * 默认保留期上限：公共存储库最多保留 **90 天**，私有存储库可配置为 **1 至 400 天**。
* **重点结论**：
  * 制品与 **GitHub Packages** 核心差异：Packages 用于管理最终发布的标准包（如 npm、Maven 库）并计收数据传输费用，而 Artifacts 仅用于内部作业流转且**不收取流量费**。

## 7.3 上传和下载制品 (Uploading and Downloading Artifacts)

* **核心知识点与关键行为**：
  * **上传**：调用官方操作 `actions/upload-artifact@v4` 将临时构建产物打包并上传到托管存储。
  * **下载**：在依赖后续作业中，调用 `actions/download-artifact@v4` 从存储中将产物拉取至当前 Runner 环境。
* **实用要点（核心参数拆解）**：
  * `name`（必需）：制品的标识符（默认值为 `artifact`）。
  * `path`（必需）：需要打包上传的文件、目录或通配符匹配路径。
  * `if-no-files-found`（可选）：未找到文件时的容错行为控制，接受 `warn`（默认，警告但不失败）、`error`（立即报错终止）、`ignore`（静默放行）。
  * `retention-days`（可选）：单独重写该次上传制品的保留天数。

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-report
    path: reports/
    retention-days: 7
```

## 7.4 在 GitHub Actions 中使用缓存 (Using Caches in GitHub Actions)

* **核心主旨**：将耗时的依赖拉取结果（如 `node_modules` 或 `~/.gradle/caches`）进行哈希缓存，从而在后续运行中实现跨步加速。
* **核心知识点与实现机理**：
  * 使用核心操作：`actions/cache@v4`。
  * **输入参数关联逻辑**：
    * `path`：定义需要被缓存或恢复的文件目录。
    * `key`：**最核心的寻址标识**，用于精准保存与恢复目标缓存。
    * `restore-keys`：**降级匹配策略**，当精确的 `key` 发生 Cache Miss 时，依据此列表进行前缀模糊恢复（此时 `cache-hit` 标志将返回 `false`）。
* **公式要点（典型缓存键设计范式）**：
  * 哈希摘要绑定：通过使用内置函数 `hashFiles` 绑定包管理依赖描述文件，确保当依赖变更时生成全新缓存键。
  * 语法示例：`key: ${{ runner.os }}-build-cache-${{ hashFiles('**/package-lock.json') }}`。
* **逻辑脉络与后续拓展**：
  * **因果流**：先以 `key` 执行搜索 → 存在则恢复并设置命中标记 → 无论是否命中均执行核心构建任务 → 若最初未精确命中，作业结束后会自动执行 `post` 步骤将新路径打包并使用当前 `key` 重新上传。
  * **拓展知识**：除了手动声明缓存外，许多高级 Setup 级别的 Action（如 `setup-java`、`setup-node`）内部已自动集成了基于包管理器的自动化缓存机制，通过简单的 `cache: 'gradle'` 配置即可开启。

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```
