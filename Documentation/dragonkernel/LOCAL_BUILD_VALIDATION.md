# 构建记录

本记录只证明构建链可生成五设备内核，不代表已经启动、兼容或可刷写。本机产物不得用于 Releases。

## 基线

- 内核提交：`0a980b6e85030a8e22a8e6446a322e4767369f9d`
- 工具链提交：`54220fd601050b350b2af7adc913089ebf0e7aed`
- 编译器：Android Clang 12.0.5 (`r416183b`)
- 环境：WSL 2 / Ubuntu 24.04 / ext4

## 本机结果

| 设备 | Image 字节数 | Image SHA-256 | DTB | DTBO | 模块 |
|---|---:|---|---:|---:|---:|
| `umi` | 55,560,208 | `e0e75831bc243ddbeeab957eca8728d10ddc9c447ddcaba3efa55000b06f23c1` | 3 | 12 | 3 |
| `cmi` | 53,467,152 | `9c4875bd56274ba74c1d3dfe3c43e6fa3bfaeb67c96c0bcc8a148ab6957b399e` | 3 | 12 | 3 |
| `cas` | 53,461,008 | `3a44faac453cb4cbef4379e6677fc2de1f82795f02091b35c36f0895b1ffe214` | 3 | 12 | 3 |
| `thyme` | 55,566,352 | `3d96f322c84a381c09011bbd8d160315d8e205f136f2b6adc37ca4270e3f8ba7` | 3 | 12 | 3 |
| `apollo` | 53,471,248 | `ca3152cb436fb21787fa472d206cec6c5b48166f6d4b2add536d6c6e17a6e2c8` | 3 | 12 | 3 |

提交 `ce0897b86aa38138761211dde7f91f4325d18005` 的历史 Original Artifact 因误启用 `CONFIG_KSU=y` 已作废。提交 `c64df02c1c7fbe76c339d50803f8ef40d4cac2c5` 修正失败传播与 Root 选择门禁后，Original、KernelSU + SUSFS、SukiSU + KPM + SUSFS 五设备矩阵均通过，运行编号分别为 `31317137033`、`31317137024`、`31317137030`；Project contract 运行 `31317137036` 通过。下载复核的 15 份 Artifact 均包含 3 个 DTB、12 个 DTBO 和 3 个模块，设备配置、变体配置与全部 `SHA256SUMS` 一致。

提交 `7afcf05a0983a3c14b964b302ef497a6153ccd34` 启用 `CONFIG_UCLAMP_TASK=y` 与 `CONFIG_UCLAMP_TASK_GROUP=y` 后，Original、KernelSU、SukiSU 五设备矩阵再次全部通过，运行编号分别为 `31321884794`、`31321884790`、`31321884791`；Project contract 运行 `31321884800` 通过。三种变体的 `cmi` Artifact 已下载复核，UCLAMP、设备与 Root 选择配置正确，结构和全部 `SHA256SUMS` 一致。

本地 boot 重打包已验证模板无修改往返、内核替换回读、分区尺寸限制和 AVB 摘要。该结果只证明镜像结构有效，不证明设备可启动。

## KernelSU 结果

- KernelSU：`v0.9.5` / `b766b98513b5a7eb33bc1c4a76b5702bf1288f07`
- 设备：`umi`
- Image：55,580,688 字节，SHA-256 `de4ff50c42c5b9eb639739b37f533019480705b5618cd8af2fbe9d81c341d2b1`
- 产物：3 个 DTB、12 个 DTBO、3 个模块
- 校验：`CONFIG_KSU=y`、`CONFIG_KPROBES=y`、`kernelsu_init` 存在，`SHA256SUMS` 全部通过

提交 `b589528db7839f786a6fa6e574f0463cc87ba1e5` 进一步在全新工作树应用锁定 SUSFS 补丁并完成 `umi` 全量构建：

- Image SHA-256：`4747ec395b1418609dfe67fa277cb837df23472a4506c7fafc60f4643adcae1f`
- 产物：3 个 DTB、12 个 DTBO、3 个模块
- 校验：`CONFIG_KSU_SUSFS=y`、隐藏符号启用、SUSFS 日志关闭、`susfs_init` 存在，`SHA256SUMS` 全部通过

该结果只证明 KernelSU + SUSFS 已集成并构建；不证明已启动、Root 可用或隐藏通过。

## SukiSU + KPM + SUSFS 结果

- SukiSU Ultra：`v4.1.3` / `0ca744a88835144c58d8256ebb32c279edabfcde`
- 设备：`umi`
- Image：55,564,304 字节，SHA-256 `42951b516af0f26a37a2cc6d368874616708d9ca48c873712110811bf53b259c`
- 产物：3 个 DTB、12 个 DTBO、3 个模块
- 校验：`CONFIG_KSU=y`、`CONFIG_KPM=y`、`CONFIG_KSU_SUSFS=y`、隐藏符号启用、SUSFS 日志关闭
- 符号：`kernelsu_init`、`susfs_init`、`ksu_susfs_handle_command` 存在

该结果只证明 Linux 4.19 兼容补丁、SukiSU、KPM、SUSFS 及管理器命令桥可完成全量构建；启动、Root 功能及三层隐藏尚未验证。

提交 `0c7bdd743b836d0cf6adc20099a7077259816b76` 已通过五设备 GitHub Actions 矩阵构建并生成五份验证 Artifact，运行编号 `31037611429`。

## 未完成

- boot.img 和可刷 ZIP
- 临时启动、冷启动和硬件矩阵
- 稳定性、性能、温度和功耗验证
