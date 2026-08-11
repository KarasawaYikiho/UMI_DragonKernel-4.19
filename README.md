# UMI DragonKernel 4.19

面向 Xiaomi SM8250 设备的 Linux 4.19 内核。基线来自 LineageOS；Xiaomi 代码仅按子系统审查后移植。

## 功能

1. WALT、schedutil、UCLAMP、Binder 优先级与 boost 所有权修正。
2. 保留 thermal zone、TSENS、BCL、LMH、冷却设备及硬件保护，移除 Xiaomi `thermal_message` 云控邮箱。
3. 可选 Dragon Adaptive Controller 模块隔离 Joyose 调度、游戏、温控和内存远程云控；保留本地系统功能。
4. 电池解容仅保留自动学习到的扩展 FCC；启动容量按型号确定，手动写入仍受原厂容量限制。
5. Baseband-guard 作为全部变体共享的防格机 LSM，独立于 Root 路径。
6. 五机型 Actions 矩阵、ccache、可复现 Image/AnyKernel3 包及 ROM 结构校验；Magisk 包复用同 SHA Original Image，不单独编译内核。

## 兼容范围

| 设备 | ROM 参考 |
|---|---|
| `umi`、`cmi`、`cas` | `Hyper3` |
| `thyme`、`apollo` | `Lineage_**Latest**` |

ROM 参考仅用于对应设备，不得跨型号复用。内核变体只有 `Original`、`Magisk`、`KernelSU`、`SukiSU_KPM_SUSFS`。

## 使用

正式产物仅由 GitHub Actions 在冻结 SHA 上重建、校验和发布。刷写前必须使用与设备和 ROM 匹配的候选包；结构检查通过不代表已启动、兼容、稳定或可发布。

Magisk Action 只把同一提交、同一机型的 Original Image 打包为 Magisk 候选包。最终 boot 必须由目标设备使用自身 ROM 经 Magisk 修补后配对，禁止跨机型复用。

本地构建仅用于必要验证，优先下载 Actions Artifact。实机验证必须等调度、温控、电池、ROM 结构和构建路径优化全部冻结后开始。

## 安全

正式 Release 必须通过最终 SHA 的全仓安全扫描、最终差异扫描、供应链审查、跨 owner/变体/ROM 冲突检查及实机回归。未解决的 Critical/High、未处置的 Medium、证据跨 SHA 或回滚不完整均阻止发布。

安全问题请通过 GitHub Security Advisory 私下报告，不要在公开 Issue 中披露利用细节或私有 ROM 信息。

## 文档

- [设备与 ROM](Documentation/dragonkernel/DEVICE_BASELINE.md)
- [功能状态](Documentation/dragonkernel/FEATURE_MATRIX.md)
- [执行流程](Documentation/dragonkernel/PROJECT_PROCESS.md)
- [构建证据](Documentation/dragonkernel/LOCAL_BUILD_VALIDATION.md)
- [优化与验证](Documentation/dragonkernel/optimization/00_REPO_AUDIT.md)
- [发布审查](Documentation/dragonkernel/optimization/09_RELEASE_REVIEW.md)

## 许可证与致谢

各文件沿用其原许可证。感谢 Linux、LineageOS、KernelSU、SukiSU、SUSFS、Magisk、AnyKernel3 与 Baseband-guard 项目贡献者。
