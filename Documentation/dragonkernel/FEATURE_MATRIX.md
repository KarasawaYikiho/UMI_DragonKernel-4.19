# 功能矩阵

状态只允许使用：`待评估`、`开发中`、`已构建`、`已启动`、`已验证`、`已发布`。

| 能力 | 计划变体 | 当前状态 | 进入条件 |
|---|---|---|---|
| LineageOS 原始基线 | all | 已构建 | 在每台目标设备上完成启动与硬件回归 |
| 小米官方驱动差异 | all | 待评估 | 按子系统确认 LineageOS 缺失项和来源提交 |
| 调度/功耗优化 | all | 待评估 | 基线数据、单变量补丁、性能/温度/续航回归 |
| Magisk | magisk | 待评估 | 使用官方 Magisk 修补已验证的 boot 镜像；内核与原版一致 |
| KernelSU | kernelsu | 待评估 | 锁定版本并验证 4.19 非 GKI 集成路径 |
| SukiSU Ultra | sukisu | 待评估 | 独立于 KernelSU 变体，锁定版本和管理器匹配关系 |
| KPM | sukisu | 待评估 | `CONFIG_KPM`、KALLSYMS、W^X 与启动稳定性审查 |
| SUSFS | sukisu | 待评估 | 锁定 4.19 适配源，检查 VFS/namespace/LSM 冲突 |
| Baseband Guard (BBG) | all | 待评估 | 锁定上游、验证 4.19 LSM 兼容性、关键分区拦截和正常刷写放行 |
| Boot 镜像 | every release | 待评估 | 提供目标 ROM 原厂镜像并通过镜像结构检查 |
| 可刷 ZIP | every release | 待评估 | 已验证 boot 镜像、设备断言、备份/回滚和校验和 |

## 变体规则

- `original`：无 root，包含通过验证的 DragonKernel 公共优化与 BBG。
- `magisk`：与原版使用同一内核二进制，仅 boot 镜像由 Magisk 修补。
- `kernelsu`：仅 KernelSU。
- `sukisu`：SukiSU Ultra，可在审核后启用 KPM/SUSFS。
- BBG 通过独立启动、分区保护、OTA/recovery/fastbootd 放行和通信回归后，并入全部四种产物。

禁止用“已支持”代替测试证据。每个状态提升必须链接构建日志、产物 SHA-256、目标 ROM、启动日志和测试记录。
