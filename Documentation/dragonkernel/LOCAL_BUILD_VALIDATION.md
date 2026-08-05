# 本机原版构建验证

本记录仅证明构建链和五个设备配置可以在 WSL 2 中生成内核产物，不代表已经启动、兼容或可刷写。本机生成的文件不得上传 Releases；正式可刷产物必须由 GitHub Actions 从干净提交重新构建并发布。

## 构建基线

- 内核提交：`0a980b6e85030a8e22a8e6446a322e4767369f9d`
- 工具链提交：`54220fd601050b350b2af7adc913089ebf0e7aed`
- 编译器：Android Clang 12.0.5，基于 `r416183b`
- 环境：WSL 2 / Ubuntu 24.04 / ext4
- 构建入口：`scripts/dragonkernel/build_original.sh <codename>`

## 结果

| 设备 | 设备配置标志 | Image 字节数 | Image SHA-256 | 配置 SHA-256 | DTB | 模块 | 结果 |
|---|---|---:|---|---|---:|---:|---|
| `umi` | `CONFIG_MACH_XIAOMI_UMI=y` | 55,560,208 | `e0e75831bc243ddbeeab957eca8728d10ddc9c447ddcaba3efa55000b06f23c1` | `32237339668240df39b30f3bd918629200592d02a8833a0d74b637ccb0bc10ce` | 3 | 3 | 通过 |
| `cmi` | `CONFIG_MACH_XIAOMI_CMI=y` | 53,467,152 | `9c4875bd56274ba74c1d3dfe3c43e6fa3bfaeb67c96c0bcc8a148ab6957b399e` | `b26283464cf54e995605ebe2ad8218535a08d500aa344ea4571b24e63b30ad7e` | 3 | 3 | 通过 |
| `cas` | `CONFIG_MACH_XIAOMI_CAS=y` | 53,461,008 | `3a44faac453cb4cbef4379e6677fc2de1f82795f02091b35c36f0895b1ffe214` | `f70a81bfb76289b10520c416fe56ed3f709f98c9ba109810d3d52dfa4c88ecc4` | 3 | 3 | 通过 |
| `thyme` | `CONFIG_MACH_XIAOMI_THYME=y` | 55,566,352 | `3d96f322c84a381c09011bbd8d160315d8e205f136f2b6adc37ca4270e3f8ba7` | `f215163a17a0c27e801b8bf4c5192934e25647ea2dc0a72384e89df6612ebe87` | 3 | 3 | 通过 |
| `apollo` | `CONFIG_MACH_XIAOMI_APOLLO=y` | 53,471,248 | `ca3152cb436fb21787fa472d206cec6c5b48166f6d4b2add536d6c6e17a6e2c8` | `1f55d55a6340e61e3e526155aae2b622f2ef7ca9be25579c20a417e7988c9a5f` | 3 | 3 | 通过 |

每台设备的本机输出均位于 WSL 的 `$HOME/out/dragonkernel/original/<codename>/`，包括 `.config`、`Image`、DTB、模块、`build.log` 和 `SHA256SUMS`。这些路径和文件只用于本机验证。

## 尚未满足的门禁

- 尚未生成或验证 DTBO 镜像；当前源码树只提供 `dtbs` 构建目标。
- 尚未生成 `boot.img` 或可刷 ZIP。
- 尚未进行临时启动、冷启动、硬件矩阵、稳定性或功耗验证。
- 当前状态不得提升为“已启动”“已验证”或“可发布”。
