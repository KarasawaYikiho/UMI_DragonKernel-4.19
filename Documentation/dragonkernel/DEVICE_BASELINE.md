# 设备与 ROM 基线

目标设备族为 SM8250 小米 10 系列。首轮矩阵为 `umi`、`cmi`、`cas`、`thyme`、`apollo`；每台设备必须使用自己的配置、设备树和启动镜像模板，禁止跨设备混刷。

## 首次真机构建前必须提供

1. 每台设备对应的私密 ROM 输入或同版本启动镜像。
2. `adb shell getprop` 完整输出。
3. `adb shell su -c 'cat /proc/config.gz'` 输出（可用时）。
4. Bootloader 是否已解锁，以及当前可用的 recovery/fastboot 恢复路径。

这些文件及其名称、版本、来源、哈希、尺寸、清单和解析元数据不得提交到仓库或输出到 CI 日志。私密输入规则见 `PRIVATE_INPUTS.md`。

## 已知的 LineageOS 构建参数

- 架构：ARM64 / Qualcomm Kona（SM8250）
- 镜像名：`Image`
- 页大小：4096
- DTB：包含在 boot 镜像中
- DTBO：独立分区
- boot header：由 ROM 形态决定，LineageOS 配置在 v2/v3 间选择
- 配置片段：
  - `vendor/kona-perf_defconfig`
  - `vendor/debugfs.config`
  - `vendor/xiaomi/sm8250-common.config`
  - `vendor/xiaomi/<codename>.config`

上述参数只是构建起点，最终必须以目标 HyperOS 3 原厂镜像解析结果为准。

## 刷写门禁

- 先验证镜像头、分区尺寸、DTB/DTBO 和 ramdisk 保持策略。
- 优先 `fastboot boot boot.img`；只有临时启动完整通过后才允许写入分区。
- 每轮测试前保留原厂镜像、校验和与恢复命令。
- 首次启动至少验证：解密、触摸、指纹、相机、音频、通话/数据、Wi-Fi/蓝牙、充电、温控、待机和重启。
