# 功能状态

状态只使用：未开始、已实现、构建通过、实机通过、已发布。

| 能力 | 当前状态 | 下一门禁 |
|---|---|---|
| 五设备 LineageOS 基线 | 构建通过 | 最终 Original 实机硬件回归 |
| WALT、schedutil、UCLAMP、前台 Binder、输入 boost | 构建通过 | 同机同 ROM 调度与交互 A/B |
| Xiaomi `thermal_message` 云控邮箱移除 | 构建通过 | TSENS、BCL、LMH、充电和过热回归 |
| 电池容量解限 | 构建通过 | 核对五机型启动容量、学习/FCC 超过原厂值和充放电回归 |
| 私有 ROM boot 结构适配工具 | 已实现 | 使用目标 ROM 与最终 Original Artifact 配对 |
| 单设备/单变体 ccache 快速构建 | 构建通过 | 实际内核源码增量提交后的缓存复用 |
| Original | 构建通过 | 五设备临时启动和硬件矩阵 |
| KernelSU + SUSFS | 构建通过 | 启动、Root、管理器与应用检测 |
| SukiSU + KPM + SUSFS | 构建通过 | 启动、Root、KPM、管理器与应用检测 |
| Magisk | 已实现 | 同机 App 修补模板、五设备结构配对、启动/Root 与三层隐藏 |
| BBG 验证叠加层 | 构建通过 | 关键分区拦截、正常系统更新和 recovery/fastboot 恢复回归 |
| 可刷 ZIP / Release | 未开始 | 恢复路径、五设备全变体和 CI 发布门禁 |

系统桌面和澎湃超级岛纳入最终交互 A/B；内核不得按应用名称添加特判。没有实机证据时，任何能力不得标记为实机通过或已发布。
