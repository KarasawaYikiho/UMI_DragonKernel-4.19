# UMI DragonKernel 4.19

面向小米 SM8250 设备的 Linux 4.19 内核，目标系统为 Android 15 / HyperOS 3。主线基于 LineageOS SM8250；小米代码只按子系统审查后移植。

## 支持范围

- 设备：`umi`、`cmi`、`cas`、`thyme`、`apollo`
- 内核：`4.19.325`
- 已构建变体：Original、KernelSU + SUSFS、SukiSU + KPM + SUSFS、BBG 验证叠加层
- 已实现本地结构链：Magisk

## 当前实现

- 保留 WALT、schedutil、UCLAMP、前台 Binder 调度、输入 boost、PSI、zram、BFQ、F2FS 与 Qualcomm 硬件温控链。
- 删除 Xiaomi `thermal_message` 用户态云控邮箱；保留 TSENS、BCL、LMH、标准 thermal zone 和硬件过热保护。
- 启动设计容量按设备型号固定：`umi`/`thyme` 4780、`cmi`/`cas` 4500、`apollo` 5000 mAh。FG Gen4 只取消重启时将高学习容量恢复为原厂值的逻辑；手动写入仍受原厂值限制，BQ 路径直接报告电量计 FCC。
- 提供单设备、单变体、带 ccache 的 Actions 快速构建，以及使用私有 ROM `boot.img` 模板的本地结构适配检查。
- 快速构建可生成固定 AnyKernel3 的 Image-only 候选 ZIP；保留目标 boot 的 ramdisk、模块、DTB/DTBO 与 vbmeta 标志，实机恢复门禁通过前不得发布。
- Magisk 复用 Original 内核；目标设备经 Magisk App 修补的私有模板只在本地合并，并校验 Magisk ramdisk 保持不变。
- BBG 仅作为 KernelSU + SUSFS 的独立验证叠加层；默认关闭，启用时保护关键分区和 boot，保留 recovery/fastboot 恢复路径。

## 验证状态

快照 `78aae4ecf28d` 已通过 Project contract，以及 Original、KernelSU、SukiSU、BBG 四个五设备 Actions 矩阵，共 20 个构建。两次同 SHA BBG/umi 快速构建生成了完全相同的 Image 与候选 ZIP；下载产物的内外层摘要、配置和打包结构复核通过。

以上只证明源码可构建和产物结构有效，不证明可启动、ROM 完全兼容、Root 隐藏、性能、温控、功耗或稳定性。实机 A/B 必须在优化作业完成后进行。

## 工作流

- 完整门禁：推送相关源码后自动构建三个内核变体和独立 BBG 叠加层的五设备矩阵。
- 快速验证：在 Actions 手动选择一个设备和一个变体，复用 ccache；不得替代完整门禁。
- 候选打包：只替换当前槽 boot 中的 Image；不携带 ramdisk、模块、DTB/DTBO 或私有 ROM 数据。
- ROM 适配：私有 ROM 只在本地提取 boot 模板；不得上传输入、模板、日志或可识别元数据。
- 正式 Release：只能由 CI 从干净提交重新编译、打包、哈希和发布。

## 文档

- [执行流程](Documentation/dragonkernel/PROJECT_PROCESS.md)
- [功能状态](Documentation/dragonkernel/FEATURE_MATRIX.md)
- [设备与 ROM 门禁](Documentation/dragonkernel/DEVICE_BASELINE.md)
- [构建证据](Documentation/dragonkernel/LOCAL_BUILD_VALIDATION.md)
- [私有输入规则](Documentation/dragonkernel/PRIVATE_INPUTS.md)
- [机器可读基线](Documentation/dragonkernel/baseline.json)
