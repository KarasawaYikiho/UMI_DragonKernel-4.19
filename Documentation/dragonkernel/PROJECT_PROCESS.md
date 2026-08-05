# 项目流程

## 基本规则

- 主线必须可构建、可启动、可回退。
- 外部补丁记录来源 URL、原提交、许可证和本地修改。
- 驱动、调度、功耗、Root 与安全能力分组引入，每次只验证一个主要变量。
- 优化必须提供性能、帧时间、温度、功耗和稳定性对比。
- 本机构建只用于验证；正式 Release 只由 CI 生成。

## 阶段

| 阶段 | 工作 | 完成条件 |
|---|---|---|
| P0 | 锁定设备、上游、工具链和私密输入边界 | `baseline.json` 与输入清单完整 |
| P1 | 复现五设备 Original 基线 | 可重复构建、临时启动、硬件回归通过 |
| P2 | 按子系统移植小米驱动差异 | 每组补丁独立构建并完成真机回归 |
| P3 | 调度、频率、内存、存储、网络与热管理优化 | 单变量数据证明收益且无稳定性回退 |
| P4 | Magisk、KernelSU、SukiSU、KPM、SUSFS、BBG | 版本锁定、安全审查和真机回归通过 |
| P5 | 生成 boot、DTBO、可刷 ZIP 与校验文件 | 五设备四变体全部打包成功 |
| P6 | CI 发布 | 同一工作流完成编译、校验、打包和 Release |

## Release 命名

时间使用 `Asia/Shanghai`，格式为 `yyyyMMddHHmm`。每个 Tag 只发布一种变体。

| 内部变体 | Release 变体名 |
|---|---|
| `original` | `Original` |
| `magisk` | `Magisk` |
| `kernelsu` | `KernelSU` |
| `sukisu-kpm-susfs` | `SukiSU_KPM_SUSFS` |

- Tag：`UMI_<yyyyMMddHHmm>_<Variant>`
- 主资产基名：`UMI_<yyyyMMddHHmm>_<Variant>_Build`
- 主资产：`<主资产基名>.zip`

示例：Tag `UMI_202608052353_KernelSU`，主资产 `UMI_202608052353_KernelSU_Build.zip`。

主资产按设备代号分目录，包含对应镜像、可刷包、配置、构建信息和 `SHA256SUMS`。额外资产必须沿用同一基名作为前缀。

## 发布门禁

- CI 检出 Tag 指向的精确提交并重新编译。
- 五台设备中任一失败时禁止发布。
- 编译、打包、SHA-256 和上传必须处于同一工作流。
- Release 记录内核提交、工具链提交、配置和工作流链接。
- 私密输入仅能通过批准的非公开通道临时注入，不得进入缓存、日志或公开元数据。
- 未完成启动和硬件回归的产物不得标记为稳定版。

## 开发环境

- 本地环境：WSL 2 / Ubuntu 24.04 / ext4。
- 源码、工具链、输出和 ccache 均保存在 WSL 文件系统。
- WSL 与 CI 使用同一锁定工具链、配置顺序和构建脚本。
