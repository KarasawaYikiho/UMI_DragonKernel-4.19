# 构建证据

验证对象：`78aae4ecf28d2e5f80e5b218a2f208f7aaedc249`。

## GitHub Actions

| 工作流 | Run | 结果 |
|---|---:|---|
| Project contract | `31379590455` | 通过，含基线、打包自检和 IKHEADERS 复现性锁 |
| Fast BBG/umi，首次 | `31379592452` | 通过；恢复跨 SHA ccache，产出 Image 与候选 ZIP 基准 |
| Fast BBG/umi，同 SHA | `31381486400` | 通过；Image 与候选 ZIP 摘要逐字节一致 |
| Original，五设备 | `31382488101` | 5/5 通过 |
| KernelSU，五设备 | `31382490698` | 5/5 通过 |
| SukiSU，五设备 | `31382492828` | 5/5 通过 |
| BBG，五设备 | `31382495072` | 5/5 通过 |

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
| BBG/umi，`78aae4ecf28d` | IKHEADERS、KSU、SUSFS、BBG、候选 ZIP | 外层摘要、21/21 内部摘要、配置、ARM64、构建日志和 13 项 ZIP 白名单通过；校验文件可移植 |
| 同 SHA 两次 BBG/umi | 构建与打包复现性 | Image 均为 `94b10f33533f2588247809261482e95ac3bebed54ee9c772612ddeac692aa751`；候选 ZIP 均为 `aae05c1b98e7e0b7b0fa127e36e17856284bec4347a5f6a6a9506b43c39a6699` |

Original/umi 来自 `66cf9d14a610`；未标 SHA 的既有代表产物来自 `8b595e6296e6`。当前 BBG/umi 来自验证对象。

`2c147a899431` 的两次同 SHA 构建曾因 `CONFIG_IKHEADERS` 归档继承 runner 文件时间而产生不同 Image。`78aae4ecf28d` 固定归档顺序、提交时间和属主后，重复构建的 Image 与候选 ZIP 一致。

## 尚未证明

- 私有 ROM 的最终结构配对与启动
- 触摸、指纹、相机、音频、通信、无线、充电和传感器回归
- 系统桌面、澎湃超级岛、帧时间、温控、功耗和稳定性 A/B
- Root 功能、管理器/注入隐藏和应用检测
- BBG 实机拦截、正常系统更新与 recovery/fastboot 恢复路径
- 候选 ZIP 的目标 ROM 配对、recovery 刷写与恢复路径
- 正式 Release

只有相应实机证据完成后，功能状态才能从“构建通过”升级为“实机通过”。
