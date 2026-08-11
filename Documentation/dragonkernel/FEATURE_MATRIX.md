# 功能状态

| 能力 | 当前状态 | 未完成门禁 |
|---|---|---|
| 五机型内核与 ROM 结构 | Actions/结构校验已通过旧冻结输入 | 安全修复后重跑最终矩阵与配对 |
| 调度与 boost | 机制和构建门禁完成 | 实机所有权、桌面/超级岛 A/B |
| 标准温控与充电保护 | 保留并通过构建门禁 | 实机热负载、充电、过热回归 |
| Joyose 远程云控隔离 | DAC `0.8.1` 已通过编译和模块 CI | 实机 UID/cgroup、流量和本地功能 |
| 电池解容 | 自动学习上限解除；启动值按型号 | 实机 FCC 学习、持久化和保护回归 |
| Original/KernelSU/SukiSU | 安全修复 SHA 的 Original/KernelSU/SukiSU/BBG 矩阵 20/20 | 代表 Artifact、ROM 配对与可复现复核 |
| Magisk | 同 SHA Original Artifact 转包通道与私有 boot 结构校验已实现 | 五机型 Action、ROM 专属修补与三层隐藏 |
| Baseband-guard | 公共 LSM；启动链缺口已修 | 全矩阵与实机写保护/恢复 |
| 可刷候选包 | Image-only AnyKernel3 已实现 | Recovery/Fastboot 刷写与回滚 |
| 安全与冲突审查 | 预实机扫描发现两项并已修 | 最终 SHA 全仓、差异、供应链、冲突复审 |
| 正式 Release | 未开始 | 所有最终 SHA 构建和实机门禁 |

内核只提供通用机制，不为桌面、超级岛或其他包名/进程名添加特判。没有实机证据的能力不得标记为稳定或可发布。
