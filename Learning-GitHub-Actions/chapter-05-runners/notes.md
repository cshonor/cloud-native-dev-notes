# 第5章：运行器 (Runners)

> **后端学习提示**：掌握 **5.1 GitHub 托管运行器** 即可；自托管、ARC、即时运行器（5.2～5.4）属运维向，可跳过。

## 5.1 GitHub 托管的运行器 (GitHub-Hosted Runners)

* **核心主旨**：阐述由 GitHub 官方提供和维护的标准化执行环境，帮助用户以最低的配置成本实现自动化的开箱即用。
* **核心知识点与关键定义**：
  * **运行器 (Runners)**：工作流中用于执行具体「作业 (Job)」的虚拟或物理计算系统。
  * **托管环境**：GitHub 提供的运行器运行在标准化的虚拟机上，涵盖预选的操作系统版本（如 Ubuntu Linux、Windows、macOS）。
* **案例数据与映射关系**：
  * 在 YAML 文件中通过 `runs-on` 关键字指定，常用标签包括 `ubuntu-latest`、`windows-latest`、`macos-latest` 等。需要注意 `latest` 指代的是 GitHub 支持的最新稳定版本，而非操作系统厂商的最新版本。
* **逻辑脉络与底层机制拆解**：
  * **查看镜像内置软件 (What's in the Runner Images?)**：为了实现供应链安全监控，系统会生成**软件物料清单 (SBOM)**。用户可以在运行日志的 `Set up job` 阶段展开 `Runner Image` 详情，通过提供的链接 (`Included Software`) 查阅当前运行器镜像预装的所有软件及版本。
  * **动态扩展软件 (Adding Additional Software)**：如果预装环境无法满足需求，由于作业拥有底层 OS 的执行权限，可直接利用标准 OS 包管理器（如 Ubuntu 的 `apt` 或 macOS 的 `brew`）在工作流 `steps` 中实时下载并安装额外软件。
* **拓展建议**：
  * 结合第 1 章成本模型：macOS 运行器计费乘数为 **10**，矩阵构建时预算消耗快，非必要不用。

```yaml
jobs:
  build:
    runs-on: ubuntu-latest   # 后端首选，成本低
    steps:
      - run: sudo apt-get update && sudo apt-get install -y jq
```

| `runs-on` | 计费乘数 | 后端常用 |
|-----------|----------|----------|
| `ubuntu-latest` | ×1 | ✅ 默认首选 |
| `windows-latest` | ×2 | 按需 |
| `macos-latest` | ×10 | 仅 iOS/macOS 构建 |

## 5.2 自托管运行器 (Self-Hosted Runners) ⏭️ 后端跳过

* **核心主旨**：讲解如何通过将私有物理机或虚拟机接入 GitHub Actions 体系，以满足特定硬件需求、网络隔离策略或控制成本。
* **核心知识点与特性对比**：
  * **自托管运行器 (Self-Hosted Runners)**：完全由用户管理配置与生命周期的系统，支持 Windows、Linux、macOS 甚至是 ARM 架构。
  * **与 GitHub 托管运行器的核心差异**：
    * **成本**：在自托管运行器上执行 Actions 任务**不消耗免费分钟数配额**（但用户需自行承担底层硬件/云资源的持有成本）。
    * **状态保留**：GitHub 托管实例在作业结束后即被销毁（Clean instance）；而自托管运行器默认是持续存在的，除非专门配置，否则上一个作业遗留的数据可能会影响下一个作业。
* **逻辑脉络与管理规范**：
  * **作用域层级 (Scope)**：自托管运行器可以绑定到三个级别：**存储库 (Repository)**（单项目专用）、**组织 (Organization)**（跨多个存储库共享）、**企业 (Enterprise)**（跨组织共享）。
  * **配置流程 (Setting Up)**：通过 `Settings > Actions > Runners` 界面获取平台专属的二进制代理程序，执行配置脚本 (`config.sh`) 并绑定生成的授权令牌 (Token)。
  * **语法要点 (Using)**：通过 `runs-on: self-hosted` 语法显式调度。
  * **标签系统 (Labels)**：系统会自动附加默认标签（如 `self-hosted`、OS 名称 `Linux/macOS`、架构 `X64/ARM64`）。支持使用多标签精准路由作业，例如 `runs-on: [self-hosted, linux, ssd]` 确保作业仅落在挂载了固态硬盘的 Linux 私有节点上。
* **易错细节与安全边界 (Security Considerations)**：
  * **权限越界风险**：自托管代理程序运行在非特权用户下，但系统通常配有无密码 `sudo` 提权能力。如果允许不可信代码（如来自外部 Fork 的 Pull Request）在自托管运行器上执行，攻击者极易通过提权获取私有网络内网的横向移动权限。
  * **生命周期宕机**：若自托管系统离线 (`Offline`) 超过 **1 天**，积压在该节点上的 Job 会由于等待超时被系统自动标记为失败 (Failed)。若超过 30 天未连接，GitHub 将自动从注册列表中注销该运行器。
* **故障排查 (Troubleshooting & Removing)**：
  * 排查通信阻断可使用自带脚本 `./run.sh --check`。安全移除需执行 `./config.sh remove --token <TOKEN>`，彻底清理残留凭证。

## 5.3 自动扩展自托管运行器 (Autoscaling Self-Hosted Runners) ⏭️ 后端跳过

* **核心主旨**：应对大规模 CI/CD 场景中自托管资源利用率不均的问题。
* **核心知识点**：
  * 通过部署 **ARC (Actions Runner Controller)** 等解决方案，结合 Kubernetes 集群，根据实时排队的作业负载数量，动态扩容或缩容 (Autoscaling) 自托管节点实例。

## 5.4 即时运行器 (Just-in-Time Runners) ⏭️ 后端跳过

* **核心主旨**：针对自托管环境引入单次销毁机制，消除「状态污染」与持久化后门风险。
* **关键定义与配置要点**：
  * **短暂性 (Ephemeral)**：通过特定配置或 REST API 调用创建的即时运行器，被强制设定为**仅执行单个作业**。作业一旦结束，该运行器实例及认证即失效销毁。此模式是实现上述 Autoscaling (ARC) 安全调度的底层基石。

## 5.5 结论 (Conclusion)

* **重点结论**：GitHub Actions 提供了两种截然不同的运行环境选择。**GitHub 托管运行器**主打零维护、跨平台与高度一致性，适合绝大多数标准流构建；**自托管运行器**提供了对底层硬件、定制化软件缓存及内网资源的绝对控制权。
* **前后因果关系**：本章明确了「代码在哪里运行」的物理与虚拟基础。环境的不同直接决定了作业间的隔离性与持久化策略，从而为下一章（第 6 章）如何利用环境变量和机密数据 (Secrets) 来管理和隔离复杂的部署环境上下文建立先决条件。

## 本章速记（后端必记）

| 概念 | 要点 |
|------|------|
| `runs-on` | 指定 Runner 类型，后端默认 `ubuntu-latest` |
| GitHub 托管 | 作业结束即销毁，干净隔离 |
| 自托管 | 不耗分钟配额，但有安全与运维成本 → **后端跳过** |
| 扩展软件 | 在 `steps` 里用 `apt`/`brew` 安装即可 |
