# DragonKernel 项目流程

## 原则

1. **能启动优先于功能数量。** 未通过原始基线前，不集成 root、隐藏或调度补丁。
2. **来源可追溯。** 外部补丁记录上游 URL、提交哈希、许可证和本地改动。
3. **一次一个变量。** 驱动、调度、内存、I/O、root 和安全特性分开验证。
4. **用数据定义“优化”。** 性能提升不能以温度、功耗、稳定性或基本硬件回归为代价。
5. **产物可回退。** 发布必须包含校验和、目标 ROM、刷写方法和恢复方法。

## P0：锁定目标（当前）

交付物：

- LineageOS、小米官方分支和提交写入 `baseline.json`。
- 明确每台设备的代号、boot header、分区尺寸和 AVB 状态。
- 保存原厂镜像及 SHA-256（镜像不进入公开 Git）。

退出条件：`DEVICE_BASELINE.md` 的输入全部齐备。

## P1：复现原始 LineageOS 基线

1. 在 WSL 2 的 Linux 文件系统中检出完整源码，不在 `/mnt/<drive>` 中编译。
2. 使用 `baseline.json` 锁定的 Clang/binutils 提交。
3. 合并 UMI 配置片段，执行 `olddefconfig`，保存最终 `.config`。
4. 构建 `Image`、DTB、DTBO 和模块，保存完整日志。
5. 使用目标 ROM 原厂 ramdisk 重打包 boot，先临时启动再刷写。

退出条件：连续三次冷启动成功，核心硬件通过，24 小时无新增 kernel panic/oops，构建可重复。

## P2：小米驱动差异

以 LineageOS 为主线，分别比较 `umi-q-oss` 和较新的 SM8250 `cmi-r-oss`。按触摸、指纹、充电、电池、相机、音频、显示、WLAN/蓝牙和热管理拆分补丁。

每组补丁都要：

- 说明 LineageOS 当前缺陷或 HyperOS 3 的实际需求；
- 保留来源提交和必要的适配说明；
- 单独构建、启动和硬件回归；
- 无明确收益的厂商代码不移植。

## P3：调度与系统优化

先采集基线，再依次处理调度、cpufreq/devfreq、热管理、内存、存储和网络。每组只允许一个主要变量。

最低数据集：

- 交互：应用冷启动、帧时间 P50/P95/P99、卡顿数；
- 性能：固定环境下的单核/多核和持续负载曲线；
- 温度：峰值、稳态、降频时间；
- 续航：固定亮屏任务与 8 小时待机掉电；
- 稳定性：24 小时压力、睡眠唤醒、充电重启和日志扫描。

没有前后数据的“优化”补丁不进入 `main`。

## P4：Root 与安全变体

按 `original`、`magisk`、`kernelsu`、`sukisu-kpm-susfs` 分开产出。Magisk 与原版共享同一内核二进制，只修补已验证的 boot 镜像。KPM、SUSFS、BBG 各自单独引入和回归，重点检查 LSM 顺序、SELinux、VFS、namespace、kallsyms、W^X 和通信功能。BBG 验证通过后进入全部四种产物。

退出条件：管理器版本匹配、卸载/升级路径可用、无权限旁路、无基本功能回归。

## P5：打包

每个变体生成：

- 原始 `Image`、DTB/DTBO（适用时）；
- 与指定 ROM 一一对应的 `boot.img`；
- 带设备和 ROM 断言的可刷 ZIP；
- `SHA256SUMS`、构建信息、配置、提交哈希和变更日志。

产物名称建议：`DragonKernel-<version>-<codename>-<variant>.zip`。公开文件名不包含私密 ROM 标识。

## P6：发布

发布候选必须从干净提交构建。先发布 `rc`，收集启动日志和硬件矩阵；稳定版只从通过全部门禁的同一提交重建。标签格式：`v<version>-umi-hyperos3`。

## Git 规则

- `main`：可启动、可回退且达到当前阶段门禁。
- 开发分支：`feature/<name>`、`driver/<subsystem>`、`sync/<upstream>`。
- 每个提交只做一类变更；外部移植在提交信息中写 `Source:` 和原提交哈希。
- LineageOS 更新走独立 `sync/*` 分支并做完整回归；小米树永不整树合并。
- 禁止提交原厂镜像、私钥、签名材料或含个人信息的设备日志。
- 禁止提交或输出私密 ROM 的名称、路径、版本、来源、哈希、文件清单和可识别元数据。

## WSL 约定

- 发行版：Ubuntu 24.04 LTS / WSL 2。
- Linux 源码、工具链、`out/` 和 ccache 全部位于发行版的 ext4.vhdx 中。
- Windows 盘只用于读取私密输入和接收最终产物。
- 环境初始化使用 `scripts/dragonkernel/bootstrap_wsl.sh`。
- WSL 与 CI 必须使用同一锁定工具链和配置片段。
