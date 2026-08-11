# 设备与 ROM

| 设备 | 启动设计容量 | ROM 参考 |
|---|---:|---|
| `umi` | 4780 mAh | `Hyper3` |
| `cmi` | 4500 mAh | `Hyper3` |
| `cas` | 4500 mAh，双电芯合计 | `Hyper3` |
| `thyme` | 4780 mAh | `Lineage_**Latest**` |
| `apollo` | 5000 mAh | `Lineage_**Latest**` |

共同基线：ARM64、Qualcomm Kona、Linux 4.19.325、4 KiB page。每个设备保留独立配置、设备树、ROM boot 模板和验证结果；任何输入不得跨型号复用。

## 结构门禁

1. 只提取目标 `boot.img`，并验证输入类型和 Image magic。
2. 只替换 boot 中的 Image；保留 ramdisk、header、AVB、分区尺寸和 ROM 自带模块策略。
3. 重打包后校验尺寸、AVB footer、内核回读、SHA 与设备标识。
4. `Lineage_**Latest**` 包和镜像目录必须解析为同一 boot。

结构门禁不证明可启动或兼容。实机阶段必须先验证最终 Original，再做桌面/超级岛 A/B、电池学习、Root/隐藏、BBG、Recovery 和回滚。
