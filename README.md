# UMI DragonKernel 4.19

面向小米 SM8250 设备的 Linux 4.19 内核，目标系统为 Android 15 / HyperOS 3。主线基于 LineageOS SM8250；小米代码只按子系统审查后移植。

## 支持范围

- 设备：`umi`、`cmi`、`cas`、`thyme`、`apollo`
- 内核：`4.19.325`
- 已构建变体：Original、KernelSU + SUSFS、SukiSU + KPM + SUSFS
- 待验证变体：Magisk、BBG

## 当前实现

- 保留 WALT、schedutil、UCLAMP、前台 Binder 调度、输入 boost、PSI、zram、BFQ、F2FS 与 Qualcomm 硬件温控链。
- 删除 Xiaomi `thermal_message` 用户态云控邮箱；保留 TSENS、BCL、LMH、标准 thermal zone 和硬件过热保护。
- 启动设计容量按设备型号固定：`umi`/`thyme` 4780、`cmi`/`cas` 4500、`apollo` 5000 mAh。FG Gen4 只解除学习容量不得高于原厂值的限制；BQ 路径直接报告电量计 FCC，不提供可写设计容量接口。
- 提供单设备、单变体、带 ccache 的 Actions 快速构建，以及使用私有 ROM `boot.img` 模板的本地结构适配检查。

## 验证状态

内核源码快照 `79f39ca6c10e` 已通过 Original、KernelSU、SukiSU 三个五设备 Actions 矩阵，共 15 个构建。Original 的 FG Gen4、单电芯 BQ、双电芯 BQ 代表产物已通过外层与内部 SHA-256、配置和构建日志复核。

以上只证明源码可构建和产物结构有效，不证明可启动、ROM 完全兼容、Root 隐藏、性能、温控、功耗或稳定性。实机 A/B 必须在优化作业完成后进行。

## 工作流

- 完整门禁：推送相关源码后自动构建三个变体的五设备矩阵。
- 快速验证：在 Actions 手动选择一个设备和一个变体，复用 ccache；不得替代完整门禁。
- ROM 适配：私有 ROM 只在本地提取 boot 模板；不得上传输入、模板、日志或可识别元数据。
- 正式 Release：只能由 CI 从干净提交重新编译、打包、哈希和发布。

## 文档

- [执行流程](Documentation/dragonkernel/PROJECT_PROCESS.md)
- [功能状态](Documentation/dragonkernel/FEATURE_MATRIX.md)
- [设备与 ROM 门禁](Documentation/dragonkernel/DEVICE_BASELINE.md)
- [构建证据](Documentation/dragonkernel/LOCAL_BUILD_VALIDATION.md)
- [私有输入规则](Documentation/dragonkernel/PRIVATE_INPUTS.md)
- [机器可读基线](Documentation/dragonkernel/baseline.json)
