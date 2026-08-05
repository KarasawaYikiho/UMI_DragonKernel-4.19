# UMI DragonKernel 4.19

面向小米 SM8250 设备和 Android 15 / HyperOS 3 的 4.19 下游内核。项目以 LineageOS SM8250 内核为主线，按需移植小米官方驱动与修复。

## 范围

- 设备：`umi`、`cmi`、`cas`、`thyme`、`apollo`
- 内核：4.19.325
- 变体：Original、Magisk、KernelSU、SukiSU + KPM + SUSFS
- Root 变体必须通过内核、管理器与应用检测三层隐藏验证。
- 公共安全能力：BBG，通过独立兼容性和真机测试后启用

## 状态

五台设备的 Original、KernelSU 及 KernelSU + SUSFS 产物已通过 GitHub Actions 矩阵构建。`umi` SukiSU + KPM 基础集成已通过 WSL 全量构建，SUSFS 接线仍在开发。本地 boot 重打包已通过内核回读、尺寸和 AVB 校验。启动、Root 隐藏、硬件、功耗及刷写兼容性尚未验证，因此当前产物不可作为正式刷机包发布。

## 构建边界

- 本机构建仅在 WSL 2 的 ext4 文件系统中执行，用于开发和验证。
- Releases 只能由 GitHub Actions 从干净提交编译、校验、打包并发布。
- 本机产物和 Actions 验证 Artifact 不得转存为 Release 资产。
- 私密输入及其可识别元数据不得进入 Git、公开日志、缓存或 Release 说明。

## 命令

```bash
git submodule update --init --recursive
bash scripts/dragonkernel/bootstrap_wsl.sh
python3 scripts/dragonkernel/verify_baseline.py
scripts/dragonkernel/build_original.sh umi
scripts/dragonkernel/prepare_susfs.sh
scripts/dragonkernel/build_kernelsu.sh umi
scripts/dragonkernel/prepare_sukisu.sh
scripts/dragonkernel/build_sukisu.sh umi
```

## 文档

- [项目流程](Documentation/dragonkernel/PROJECT_PROCESS.md)
- [功能矩阵](Documentation/dragonkernel/FEATURE_MATRIX.md)
- [设备基线](Documentation/dragonkernel/DEVICE_BASELINE.md)
- [本机构建记录](Documentation/dragonkernel/LOCAL_BUILD_VALIDATION.md)
- [私密输入规则](Documentation/dragonkernel/PRIVATE_INPUTS.md)
- [机器可读基线](Documentation/dragonkernel/baseline.json)

首次真机测试必须优先临时启动，并保留已验证的恢复路径。
