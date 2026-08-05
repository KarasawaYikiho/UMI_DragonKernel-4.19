# Original 构建记录

本记录只证明构建链可生成五设备内核，不代表已经启动、兼容或可刷写。本机产物不得用于 Releases。

## 基线

- 内核提交：`0a980b6e85030a8e22a8e6446a322e4767369f9d`
- 工具链提交：`54220fd601050b350b2af7adc913089ebf0e7aed`
- 编译器：Android Clang 12.0.5 (`r416183b`)
- 环境：WSL 2 / Ubuntu 24.04 / ext4

## 本机结果

| 设备 | Image 字节数 | Image SHA-256 | DTB | 模块 |
|---|---:|---|---:|---:|
| `umi` | 55,560,208 | `e0e75831bc243ddbeeab957eca8728d10ddc9c447ddcaba3efa55000b06f23c1` | 3 | 3 |
| `cmi` | 53,467,152 | `9c4875bd56274ba74c1d3dfe3c43e6fa3bfaeb67c96c0bcc8a148ab6957b399e` | 3 | 3 |
| `cas` | 53,461,008 | `3a44faac453cb4cbef4379e6677fc2de1f82795f02091b35c36f0895b1ffe214` | 3 | 3 |
| `thyme` | 55,566,352 | `3d96f322c84a381c09011bbd8d160315d8e205f136f2b6adc37ca4270e3f8ba7` | 3 | 3 |
| `apollo` | 53,471,248 | `ca3152cb436fb21787fa472d206cec6c5b48166f6d4b2add536d6c6e17a6e2c8` | 3 | 3 |

提交 `559f31fa3c2f2e8af0d0a18304e0e5a5336ef594` 已通过五设备 GitHub Actions 干净重建，并生成五份短期验证 Artifact。

本地 boot 重打包已验证模板无修改往返、内核替换回读、分区尺寸限制和 AVB 摘要。该结果只证明镜像结构有效，不证明设备可启动。

## 未完成

- DTBO、boot.img 和可刷 ZIP
- 临时启动、冷启动和硬件矩阵
- 稳定性、性能、温度和功耗验证
