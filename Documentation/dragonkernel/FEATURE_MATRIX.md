# 功能状态

| 能力 | 状态 | 下一门禁 |
|---|---|---|
| 五机型内核基线 | 构建通过 | 最终 Original 实机回归 |
| WALT/schedutil/UCLAMP/Binder/boost | 构建通过 | 桌面与澎湃超级岛同机 A/B |
| 标准温控与充电保护 | 构建通过 | 实机热负载、充电和过热回归 |
| Xiaomi `thermal_message` 云控删除 | 构建通过 | 确认标准保护链无回退 |
| Joyose 调度等远程云控隔离 | 已完成源码边界审计 | 运行时定位远程配置与实际写入 owner |
| DAC + 统一 ROOT 管理器模块 | 原生安全骨架、模块与可复现打包已实现 | CI arm64 构建与产物复核 |
| 电池解容 | 构建通过 | 启动容量、学习 FCC、持久化和保护回归 |
| Original | 五机型构建通过 | 五机型实机矩阵 |
| KernelSU + SUSFS | 五机型构建通过 | Root、管理器、注入与应用检测 |
| SukiSU + KPM + SUSFS | 五机型构建通过 | Root、KPM、管理器、注入与应用检测 |
| Magisk | 结构链已实现 | 每机型专属模板与三层隐藏验证 |
| Baseband-guard 防格机 | 公共功能已修正 | 五机型独立矩阵及各变体配置/对象复核 |
| Image-only 候选 ZIP | 构建通过 | Recovery 刷写与回滚 |
| `Hyper3` ROM 结构 | `umi`/`cmi`/`cas` 通过 | 最终提交重新配对 |
| `Lineage_**Latest**` ROM 结构 | `thyme`/`apollo` 通过 | 最终提交重新配对 |
| 正式 Release | 未开始 | 全部实机门禁通过 |

内核优化只使用通用机制，不按包名或进程名特判系统桌面、澎湃超级岛或其他软件。没有实机证据的能力不得标记为实机通过或已发布。
