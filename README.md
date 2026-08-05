# UMI DragonKernel 4.19

面向 SM8250 小米 10 系列和中国版 HyperOS 3 的 Android 4.19 下游内核。

本项目以 LineageOS 的 SM8250 4.19 内核为主线，按需移植小米官方开源树中的设备驱动与修复。性能、续航和新特性必须以可复现构建、真机数据和可回退刷写为前提。

## 当前状态

- 阶段：P0 多设备基线初始化
- 设备：`umi`、`cmi`、`cas`、`thyme`、`apollo`
- 内核：4.19.325
- LineageOS 基线：`lineage-23.2` / `71b13e62f057a649b77fe4062feb73ee72ad609c`
- 小米参考：`umi-q-oss` / `db67ca6001320efc1f945c270635434fc403a9d4`
- 已确认配置：Kona 公共配置 + 对应设备的 `vendor/xiaomi/<codename>.config`
- 构建、启动、HyperOS 3 兼容性：尚未验证

任何 `boot.img` 或刷机包在通过真机门禁前都不得标记为稳定版。

## 设计边界

- `main` 只接收已通过对应阶段门禁的变更。
- 小米官方树不整树合并；驱动和修复按子系统、按提交移植并记录来源。
- 调度、电源、内存和 I/O 优化一次只改变一个变量，并保留前后数据。
- 每台设备发布四种产物：原版、Magisk、KernelSU、SukiSU+KPM+SUSFS。
- Magisk 只改变启动镜像，内核二进制与同版本原版一致。
- KernelSU 与 SukiSU Ultra 使用独立构建变体，不在同一内核中叠加。
- Baseband Guard（BBG）作为四种产物的共同防格机能力，但必须先完成 4.19 兼容性、安全审查和真机拦截/放行测试。
- 私密 ROM、镜像、哈希、文件清单和可识别元数据禁止进入 Git、CI 日志和公开发布说明。

## 文档

- [项目流程](Documentation/dragonkernel/PROJECT_PROCESS.md)
- [功能矩阵](Documentation/dragonkernel/FEATURE_MATRIX.md)
- [设备与 ROM 输入](Documentation/dragonkernel/DEVICE_BASELINE.md)
- [私密输入规则](Documentation/dragonkernel/PRIVATE_INPUTS.md)
- [可机读基线锁](Documentation/dragonkernel/baseline.json)

运行项目契约检查：

```bash
python3 scripts/dragonkernel/verify_baseline.py
```

WSL 2 环境初始化：

```bash
bash scripts/dragonkernel/bootstrap_wsl.sh
```

> 刷写内核有无法启动或丢失数据的风险。开发阶段应优先使用 `fastboot boot` 临时启动，并始终保留已验证的原厂镜像和恢复路径。
