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
| Magisk 路径 | `396fa620b131` 的五机型同 SHA Original 转包 5/5；下载后逐机型核对 13 成员包、Root-none/BBG、ARM64 与实际 Image SHA 全部通过 |
| 代表 Root/BBG 产物 | `c87b3a7694df` 的 KernelSU、SukiSU、BBG/umi 外层 ZIP、21/21 内部 SHA、配置、ARM64、DTB/DTBO/模块与日志通过 |
| 当前可复现性 | `dbd46913cb65` 两次 Original/umi Action 的 Image、候选 ZIP、配置与确定性成员一致；仅运行日志不同 |
| 当前 ROM 结构 | `396fa620b131` 五机型 Original Artifact 与对应公开 ROM 档案结构配对 5/5 通过 |

## 当前失效与进行中

BBG 修复改变公共内核输入，`11067a49997e` 的 20 个内核产物仅保留为历史证据。安全修复后的矩阵、代表 Artifact、Magisk 同 SHA 转包、当前 ROM 结构配对与精确 SHA 可复现检查均已通过。

## 尚未证明

未开始实机启动、兼容、性能、桌面/超级岛 A/B、温控、功耗、电池扩容学习、Root 隐藏、BBG 写保护、Recovery/Fastboot、回滚和长期稳定验证。正式 Release 还需在最终设备证据后重新执行全仓多轮安全、最终差异、供应链和冲突审查。
