# UMI DragonKernel 4.19

面向小米 SM8250 设备的 Linux 4.19 内核。主线基于 LineageOS SM8250；小米代码仅按子系统审查后移植。

## 范围

- 设备：`umi`、`cmi`、`cas`、`thyme`、`apollo`
- 系统参考：`umi`/`cmi`/`cas` 使用 `Hyper3`；`thyme`/`apollo` 使用 `Lineage_**Latest**`
- `Lineage_**Latest**` 包与对应镜像目录必须指向同一 boot 模板；`thyme` 与 `apollo` 各保留一个档案
- 变体：Original、Magisk、KernelSU + SUSFS、SukiSU + KPM + SUSFS

## 已实现

- WALT、schedutil、UCLAMP、Binder 优先级、输入 boost 与全局 boost 的机制级调度修正
- 删除 Xiaomi `thermal_message` 用户态云控邮箱；保留 thermal zone、TSENS、BCL、LMH、冷却设备和硬件保护
- Joyose 调度等云控已纳入 DAC 所有权审计；未验证远程拦截点前只观察、不启用阻断
- Baseband-guard 作为所有变体共享的防格机 LSM；它不是 Root 变体，并有独立功能矩阵
- 电池解容只保留自动学习到的高于原厂容量；启动容量按机型确定，手动写入仍受原厂值限制，电压、电流、认证和温度保护不变
- GitHub Actions 五机型矩阵、单设备快速构建、ccache、可复现 Image/AnyKernel3 候选包
- ROM boot 直接提取及 OTA payload 的单分区提取；本地完成设备专属重打包、AVB/尺寸与内核回读检查

## 当前证据

源代码快照 `08f410eb5242` 的 Project contract、Original、KernelSU、SukiSU 与独立 BBG 公共功能矩阵通过，共 20/20。旧 BBG 组合证据因错误依赖 KernelSU/SUSFS 已作废。Original/umi 的既有同 SHA 复现和五机型 ROM 结构配对仍须随最终 Image 重跑。

这些结果只证明源码、构建产物和 ROM 结构门禁有效，不代表已启动、兼容、稳定或可发布。调度、温控、电池、ROM 结构和快速构建全部冻结后，才进入实机验证。

## 文档

- [执行流程](Documentation/dragonkernel/PROJECT_PROCESS.md)
- [功能状态](Documentation/dragonkernel/FEATURE_MATRIX.md)
- [设备与 ROM 门禁](Documentation/dragonkernel/DEVICE_BASELINE.md)
- [构建证据](Documentation/dragonkernel/LOCAL_BUILD_VALIDATION.md)
- [私有输入规则](Documentation/dragonkernel/PRIVATE_INPUTS.md)
- [机器可读基线](Documentation/dragonkernel/baseline.json)
- [优化审计与验证](Documentation/dragonkernel/optimization/00_REPO_AUDIT.md)
