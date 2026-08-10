# 构建证据

验证对象：`24b44c49fa3e051de30270debf800c3aac2139d1`。

## GitHub Actions

| 工作流 | Run | 结果 |
|---|---:|---|
| Project contract | `31371191192` | 通过，含基线、BBG 隔离和 Magisk ramdisk 自检 |
| Original，五设备 | `31371190792` | 5/5 通过 |
| KernelSU，五设备 | `31371191827` | 5/5 通过 |
| SukiSU，五设备 | `31371191441` | 5/5 通过 |
| BBG，五设备 | `31371190895` | 5/5 通过 |

本轮未执行本地内核编译。

## 下载产物复核

| 产物 | 覆盖驱动 | 结果 |
|---|---|---|
| Original/umi，`66cf9d14a610` | Qualcomm FG Gen4、容量学习、Magisk 内核来源 | 外层 SHA-256、21 项内部摘要、设备/Root-none/UCLAMP 配置和两个驱动对象通过；构建日志无错误 |
| Original/cmi | 单电芯 BQ27Z561 | 外层 SHA-256、21 项内部摘要、设备配置和驱动对象通过；构建日志无错误 |
| Original/cas | 双电芯 BQ27Z561 | 外层 SHA-256、21 项内部摘要、设备配置和驱动对象通过；构建日志无错误 |
| SukiSU/cmi | KSU、KPM、SUSFS、单电芯 BQ27Z561 | 外层 SHA-256、21 项内部摘要、变体/设备配置和驱动对象通过；构建日志无错误 |
| KernelSU/cas | KSU、SUSFS、双电芯 BQ27Z561 | 外层 SHA-256、21 项内部摘要、变体/设备配置和驱动对象通过；构建日志无错误 |
| Fast Original/umi，`8b595e6296e6` | ccache 快速路径 | 外层 SHA-256、21 项内部摘要、Original/umi 配置、UCLAMP 和两个 FG 对象通过；构建日志无错误 |
| BBG/umi，`24b44c49fa3e` | KSU、SUSFS、BBG、Qualcomm FG Gen4 | 外层 SHA-256、21 项内部摘要、设备/UCLAMP/Root/BBG 配置、ARM64 标记和驱动对象通过；构建日志无错误 |

Original/umi 来自 `66cf9d14a610`；未标 SHA 的既有代表产物来自 `8b595e6296e6`。本轮 BBG/umi 来自当前验证对象。

## 尚未证明

- 私有 ROM 的最终结构配对与启动
- 触摸、指纹、相机、音频、通信、无线、充电和传感器回归
- 系统桌面、澎湃超级岛、帧时间、温控、功耗和稳定性 A/B
- Root 功能、管理器/注入隐藏和应用检测
- BBG 实机拦截、正常系统更新与 recovery/fastboot 恢复路径
- 可刷 ZIP 和正式 Release

只有相应实机证据完成后，功能状态才能从“构建通过”升级为“实机通过”。
