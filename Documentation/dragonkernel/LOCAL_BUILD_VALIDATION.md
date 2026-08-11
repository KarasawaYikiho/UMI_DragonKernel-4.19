# 构建证据

验证源码：`46575b0b43f63d62c83ff7ceb48de15cb6b6eab3`。本轮未执行本地内核编译。

## GitHub Actions

| 工作流 | Run | 结果 |
|---|---:|---|
| Project contract | `31468231063` | 通过 |
| Original 五机型 | `31468231097` | 5/5 |
| KernelSU 五机型 | `31468231024` | 5/5 |
| SukiSU 五机型 | `31468231011` | 5/5 |
| BBG 五机型 | `31468230988` | 5/5 |
| Fast Original/cmi | `31468350136` | 通过 |
| Fast Original/umi | `31469006252` | 通过 |
| Fast Original/umi，同 SHA 重复 | `31470315829` | 通过 |
| Fast Original/cas | `31470217678` | 通过 |
| Fast Original/thyme | `31471684131` | 通过 |
| Fast Original/apollo | `31471686271` | 通过 |

## 下载产物复核

- Original/cmi、Fast Original/umi、cmi、cas：内部 21/21 摘要、候选 ZIP 摘要、设备/Root-none/UCLAMP/schedutil/thermal 配置、ARM64 Image、当前 release/SHA 和设备充电驱动对象通过。
- `umi`、`cmi`、`cas`：分别使用对应 `Hyper3` 模板完成重打包、AVB/尺寸和内核回读检查。
- `thyme`、`apollo`：各自的新 `Lineage_**Latest**` 包与镜像目录 boot 一致；两项 Artifact 均通过 21/21 摘要、配置、候选包和对象日志复核，并完成结构配对。
- Original/umi 两次同 SHA 构建完全一致：Image `b4e24162b499aef5973025cde364d6eb173f38c90fd01b3967f20a4ea6236ca0`；候选 ZIP `5d4648bee33fa3a8d3fbc9cff4b2a2acf413dc90375bcdc5af831e0a444c8e71`。
- 下载临时目录已删除；仅保留被 Git 忽略的本地私有结构验证输出。

待当前文档与 OTA payload 路径提交后，最终 SHA 必须重新通过 Project contract、四个五机型矩阵、五机型快速 Original、同 SHA 复现及全部 ROM 档案结构门禁。

## 尚未证明

启动、硬件兼容、调度收益、桌面/澎湃超级岛表现、温控、功耗、扩容学习、Root 隐藏、BBG、Recovery 刷写、长期稳定性和 Release 均等待优化冻结后的实机证据。
