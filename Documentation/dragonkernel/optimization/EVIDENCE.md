# 当前证据

## 已通过

| 范围 | 证据 |
|---|---|
| 公共内核输入 | `11067a49997e` 的 Original、KernelSU、SukiSU、独立 Root-none BBG 五机型矩阵共 20/20 |
| 构建复现 | Original/umi 同 SHA 的 Image 与候选 ZIP 一致；ccache 跨 SHA 命中通过 |
| ROM 结构 | `umi`/`cmi`/`cas` 的 `Hyper3` 与 `thyme`/`apollo` 的 `Lineage_**Latest**` 配对通过 |
| DAC 0.8.0 | `45dccdd7d84f` 的 host/Android 编译、确定性打包、下载 Artifact 独立校验通过 |
| 设备采集器 | `0e24dac61e98` 的只读探针、自检与 Project contract 通过 |
| 文档门禁 | `15e26be967d5` 的 Project contract 通过；内核输入未变 |
| 安全差异检查 | `08f410eb5242..28f51f3e0382`，24/24 收据，0 项报告 |
| 预实机标准安全扫描 | `d51a28b3-a9b4-4201-ab33-00472cf25b51` 在 `15e26be967d5` 报告 BBG High 与 DAC Medium 两项 |
| 安全修复 | `c87b3a7694df` 修正完整 boot-chain 保护与 Joyose UID+cmdline 身份；Project、DAC 0.8.1 与四组五机型矩阵 20/20 通过 |
| Magisk 路径 | 同 SHA Original Artifact 转包、Image 一致性和 Root-none 门禁已实现；五机型 Action 待跑 |

## 当前失效与进行中

BBG 修复改变公共内核输入，`11067a49997e` 的 20 个内核产物仅保留为历史证据。`c87b3a7694df` 的 Original、KernelSU、SukiSU、BBG 五机型矩阵已通过；仍需 Magisk 同 SHA 转包、代表 Artifact、ROM 结构与可复现复核。

## 尚未证明

未开始实机启动、兼容、性能、桌面/超级岛 A/B、温控、功耗、电池扩容学习、Root 隐藏、BBG 写保护、Recovery/Fastboot、回滚和长期稳定验证。正式 Release 还需在最终设备证据后重新执行全仓多轮安全、最终差异、供应链和冲突审查。
