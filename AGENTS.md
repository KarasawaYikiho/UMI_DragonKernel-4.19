# DragonKernel 仓库代理约定

本文件适用于整个仓库。任何代理、脚本设计和代码变更都必须遵守以下约定。

## 项目定位

- 项目名称：UMI DragonKernel 4.19。
- 目标平台：小米 SM8250 系列，设备代号固定为 `umi`、`cmi`、`cas`、`thyme`、`apollo`。
- 目标系统：中国版 HyperOS 3 形态，Android 15。
- 内核主线：LineageOS `android_kernel_xiaomi_sm8250` 的 4.19 分支。
- 驱动来源：小米官方 `Xiaomi_Kernel_OpenSource`；只按需移植驱动和修复，禁止整树合并。
- 目标是在可启动、稳定、低功耗和可回退的前提下实现高性能调度与系统优化，并审慎引入新内核技术。
- 维护者：Karasawa `<2339725024@qq.com>`。

精确上游分支、提交和工具链以 `Documentation/dragonkernel/baseline.json` 为唯一机器可读基线，禁止在脚本中维护冲突的第二份版本表。

## 严格保密边界

- 私密 ROM 仅作为本机适配输入，禁止进入 Git、Git LFS、Actions 缓存、Artifacts、日志、提交信息、Issue、PR、Release 说明或公开产物元数据。
- 禁止输出或记录私密 ROM 的名称、路径、版本、来源、哈希、大小、文件清单及任何可识别元数据。
- 可以提交为兼容性而编写的通用代码，但代码、注释和测试数据不得反向暴露私密输入身份。
- 原始镜像、设备日志、密钥、签名材料和个人数据必须留在忽略目录或仓库之外。
- 不确定某项信息是否可公开时必须先询问维护者。

## 构建环境与职责分离

- 内核只能在 WSL 2 的 Ubuntu 24.04 Linux 文件系统中编译，禁止在 `/mnt/<drive>` 或 Windows 文件系统上编译。
- 源码、锁定工具链、`out/` 和 ccache 必须位于 WSL ext4.vhdx。
- 本机编译只用于开发、测试、故障定位和验证；本机产物不得上传 Releases。
- Releases 中的正式可刷产物只能由 GitHub Actions 从干净提交重新编译、校验、打包并直接发布。
- WSL 与 CI 必须使用同一锁定工具链、配置片段顺序和构建脚本。
- 正式发布链必须在同一次工作流中完成编译、打包、SHA-256、元数据生成和 Release 上传；任一设备或变体失败时禁止发布不完整版本。

## 产物矩阵

每台设备最终必须提供四种相互独立的产物：

1. `original`：无 root 的 DragonKernel。
2. `magisk`：与同版本 `original` 使用完全相同的内核二进制，只由 Magisk 修补已验证的启动镜像。
3. `kernelsu`：仅集成已锁定并验证的 KernelSU。
4. `sukisu-kpm-susfs`：SukiSU Ultra + KPM + SUSFS，独立于 KernelSU 变体。

所有变体在 BBG 完成单独兼容性、安全性和真机回归后共同包含 Baseband Guard 防格机能力。正式产物包括适用设备的 `Image`、DTB/DTBO、`boot.img` 或可刷 ZIP、`SHA256SUMS`、配置、构建提交和变更日志。

## 实施顺序

1. 先复现五台设备的无修改 `original` 基线构建和启动。
2. 再按子系统移植缺失的小米官方驱动，每组补丁单独构建和真机回归。
3. 采集基线数据后再处理调度、cpufreq/devfreq、热管理、内存、存储和网络优化。
4. 原版稳定后再分别引入 KernelSU、SukiSU、KPM、SUSFS 和 BBG。
5. 最后建立 CI 可刷包和 Releases 发布链。

未通过当前阶段前禁止提前叠加后续特性。外部项目必须锁定 URL、提交、许可证和本地改动；不得使用不固定版本的在线安装脚本。

## 质量与安全门禁

- “已支持”必须有构建日志、产物 SHA-256、目标设备启动记录和硬件回归证据，禁止以配置项存在代替验证。
- 优化必须提供变更前后数据，至少覆盖性能、帧时间、温度、功耗和稳定性；无明确收益的补丁不进入 `main`。
- 每次只改变一个主要变量，优先修复共享根因，不为未来需求预建抽象。
- Root 和隐藏相关变更必须审查 LSM 顺序、SELinux、VFS、namespace、kallsyms、W^X、权限旁路和卸载/升级路径。
- BBG 必须同时验证关键分区拦截，以及 OTA、recovery、fastbootd 和正常通信场景的正确放行。
- 首次刷写必须优先临时启动，确认镜像头、分区尺寸、DTB/DTBO、AVB 和恢复路径后才允许写入分区。
- `main` 必须保持可构建、可启动、可回退；外部移植提交信息必须包含 `Source:` 和原始提交哈希。

## 仓库历史边界

- 当前仓库是独立的 4.19 项目，只能继承本文明确列出的上游。
- 禁止恢复、引用或混入任何已废弃仓库的历史、远端、文件、命名、兼容层、提交或产物。

## 常用入口

- 基线检查：`python3 scripts/dragonkernel/verify_baseline.py`
- WSL 初始化：`bash scripts/dragonkernel/bootstrap_wsl.sh`
- 本机原版验证构建：`scripts/dragonkernel/build_original.sh <codename>`
- 完整阶段与发布规则：`Documentation/dragonkernel/PROJECT_PROCESS.md`

遇到无法从源码、锁定基线或本机输入安全确定的设备特定选择时，停止猜测并询问维护者。
