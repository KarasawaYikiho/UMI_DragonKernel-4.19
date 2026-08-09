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

## 刷写门禁

- 验证镜像头、分区尺寸、DTB/DTBO、ramdisk 和 AVB。
- 优先使用临时启动；完整通过后才允许写入分区。
- 保留已验证的恢复镜像、校验和与恢复命令。
- 回归解密、触摸、指纹、相机、音频、通信、无线、充电、温控、待机和重启。

## 系统交互性能基线

- 场景：系统桌面冷/热启动、连续滑页、组件滚动、文件夹开合、最近任务、应用启动与手势回桌面。
- 特殊场景：澎湃超级岛展开、收起、动画切换，以及通知、通话、媒体和下载状态的连续更新。
- 指标：帧时间 P50/P95/P99、卡顿与冻结帧、输入到显示延迟、CPU 频率与驻留、唤醒与迁移、内存 PSI/回收、温度和功耗。
- 方法：固定 ROM、温度、电量、动画设置、后台进程与操作脚本；预热后至少重复三轮，保留原始 trace 和汇总结果。
- 门禁：优化前后做同机 A/B；不得以更高温度、功耗、后台重载或稳定性回退换取短时流畅度。
