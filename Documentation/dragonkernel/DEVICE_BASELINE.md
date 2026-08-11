# 设备与 ROM 门禁

| 设备 | 启动设计容量 | ROM 参考 | 档案要求 |
|---|---:|---|---|
| `umi` | 4780 mAh | `Hyper3` | 独立 |
| `cmi` | 4500 mAh | `Hyper3` | 独立 |
| `cas` | 4500 mAh，双电芯合计 | `Hyper3` | 独立 |
| `thyme` | 4780 mAh | `Lineage_**Latest**` | 独立替代参考 |
| `apollo` | 5000 mAh | `Lineage_**Latest**` | 独立替代参考 |

共同基线为 ARM64、Qualcomm Kona、Linux 4.19.325、4 KiB page 和 Android Clang r416183b。配置、设备树、boot 模板和验证输出不得跨型号或跨档案复用。

## 结构门禁

1. 从 raw boot、归档或 OTA payload 中只提取目标 `boot.img`。
2. 下载同一提交、同一设备的 Original Actions Artifact，校验摘要、配置、Image 和构建对象。
3. 只替换目标 boot 中的 Image；保留 ramdisk、header、AVB 参数、分区尺寸、模块和 DTB/DTBO 策略。
4. 重打包后校验尺寸、AVB footer 和内核回读。
5. `Lineage_**Latest**` 包与镜像目录中的 boot 必须一致；`thyme` 和 `apollo` 各输出一个结果。

结构门禁通过不等于可启动或 ROM 兼容。

## 实机门禁

实机验证仅在调度、温控、电池、ROM 结构和构建路径全部完成后开始，并先验证最终 Original：

- 安全启动、回滚、解密、触摸、指纹、相机、音频、通信、无线、充电、传感器、待机与重启
- 同设备同 ROM 的系统桌面与澎湃超级岛 A/B；记录帧时间 P50/P95/P99、卡顿、输入延迟、CPU 驻留、迁移、PSI、温度、功耗和稳定性
- 核对机型启动容量及扩容电池学习/FCC；不得绕过任何电气、认证或温度保护
- Original 通过后才验证 Root 变体与刷写包；Baseband-guard 作为公共功能在每条路径复核写保护和恢复

任何关键回退都会关闭实机门禁并返回源码优化阶段。
