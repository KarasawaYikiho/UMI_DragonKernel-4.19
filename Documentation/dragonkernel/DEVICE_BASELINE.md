# 设备基线

## 目标设备

`umi`、`cmi`、`cas`、`thyme`、`apollo`。每台设备必须使用自己的配置、设备树和启动镜像模板，禁止跨设备混用。

## 构建参数

- 架构：ARM64 / Qualcomm Kona
- 内核镜像：`Image`
- 页面大小：4096
- 配置顺序：
  1. `vendor/kona-perf_defconfig`
  2. `vendor/debugfs.config`
  3. `vendor/xiaomi/sm8250-common.config`
  4. `vendor/xiaomi/<codename>.config`
  5. `olddefconfig`

boot header、分区尺寸、DTB/DTBO、ramdisk 和 AVB 参数必须从目标设备输入验证，不能仅依赖 LineageOS 默认值。

## 真机输入

- 对应设备的启动镜像输入
- `getprop` 输出
- `/proc/config.gz`，如可读取
- Bootloader 状态和可用恢复路径

所有输入均受 [私密输入规则](PRIVATE_INPUTS.md) 约束。

## ROM 适配流程

- 通过 `prepare_rom_boot.sh` 从本地 ROM 包提取私有 boot 模板，不记录输入身份、路径、版本、哈希或归档清单。
- 下载目标提交的 Actions Artifact 后，通过 `validate_rom_artifact.sh` 将对应设备的 `Image` 写入该模板。
- 重打包必须保留 ROM 原有 ramdisk、boot 头部和 AVB 参数，并通过内核回读与分区尺寸检查。
- stock DTBO、vendor_boot 和 vendor_dlkm 默认保持不变；只有取得明确的设备树或模块 ABI 证据后才允许替换。
- 结构校验不能代替启动、硬件、系统桌面、澎湃超级岛、温控和电池实机验证。

## 刷写门禁

实机验证统一安排在优化作业完成后，使用最终 Original CI 产物执行。

- 验证镜像头、分区尺寸、DTB/DTBO、ramdisk 和 AVB。
- 优先使用临时启动；完整通过后才允许写入分区。
- 保留已验证的恢复镜像、校验和与恢复命令。
- 回归解密、触摸、指纹、相机、音频、通信、无线、充电、温控、待机和重启。
- 解容验证从原厂设计容量开始，逐级写入目标容量；确认重启恢复原厂值，且不得改变充电电压、电流、认证和温度保护。

## 系统交互性能基线

- 场景：系统桌面冷/热启动、连续滑页、组件滚动、文件夹开合、最近任务、应用启动与手势回桌面。
- 特殊场景：澎湃超级岛展开、收起、动画切换，以及通知、通话、媒体和下载状态的连续更新。
- 指标：帧时间 P50/P95/P99、卡顿与冻结帧、输入到显示延迟、CPU 频率与驻留、唤醒与迁移、内存 PSI/回收、温度和功耗。
- 方法：固定 ROM、温度、电量、动画设置、后台进程与操作脚本；预热后至少重复三轮，保留原始 trace 和汇总结果。
- 门禁：优化前后做同机 A/B；不得以更高温度、功耗、后台重载或稳定性回退换取短时流畅度。
