# 设备与 ROM 门禁

## 设备

| 设备 | 配置 |
|---|---|
| `umi` | `arch/arm64/configs/vendor/xiaomi/umi.config` |
| `cmi` | `arch/arm64/configs/vendor/xiaomi/cmi.config` |
| `cas` | `arch/arm64/configs/vendor/xiaomi/cas.config` |
| `thyme` | `arch/arm64/configs/vendor/xiaomi/thyme.config` |
| `apollo` | `arch/arm64/configs/vendor/xiaomi/apollo.config` |

共同基线：ARM64 / Qualcomm Kona、Linux `4.19.325`、4 KiB page、Android Clang `r416183b`。每台设备必须使用自己的配置、设备树和 boot 模板。

## ROM 结构适配

1. `prepare_rom_boot.sh` 从私有 raw boot、ZIP、TAR 或 TGZ 中提取唯一的 `boot.img`。
2. 从目标提交的 Actions Artifact 取得对应设备 `Image` 和 `.config`。
3. `validate_rom_artifact.sh` 校验设备配置和 ARM64 Image，再替换私有模板中的内核。
4. 重打包必须保留 ROM ramdisk、boot header、AVB 参数和分区尺寸，并通过内核回读。
5. stock DTBO、`vendor_boot` 和 `vendor_dlkm` 默认不变；没有设备树或模块 ABI 证据时禁止替换。

结构适配通过不等于可启动或兼容。

## 实机门禁

实机阶段只能在优化作业完成后，使用最终 Original CI 产物开始：

1. 校验设备、镜像头、分区尺寸、DTB/DTBO、ramdisk 和 AVB。
2. 优先临时启动；保留已验证恢复镜像和恢复命令。
3. 回归解密、触摸、指纹、相机、音频、通信、无线、充电、温控、待机、重启和传感器。
4. 固定 ROM、温度、电量、动画、后台进程和操作脚本，执行同机 A/B。
5. 覆盖桌面冷/热启动、滑页、组件、文件夹、最近任务、应用启动、手势回桌面，以及澎湃超级岛展开、收起、动画和连续状态更新。
6. 记录帧时间 P50/P95/P99、卡顿、输入延迟、CPU 频率/驻留、唤醒/迁移、内存 PSI、温度、功耗和稳定性。
7. 电池容量从原厂设计值逐级调整，确认重启恢复原值且充电电压、电流、认证和温度保护不变。

任何温度、功耗、后台负载、硬件功能或稳定性回退都阻止进入 Root 变体和 Release。
