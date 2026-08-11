# 构建证据

本地未编译内核。验证优先使用 GitHub Actions 与下载 Artifact。

## 已确认

- 内核输入 `11067a49997e`：Original、KernelSU、SukiSU、独立 Root-none BBG 共 20/20 五机型任务通过。
- Original/umi：同 SHA 的 Image 与候选 ZIP 可复现。
- 五机型：对应 `Hyper3` 或 `Lineage_**Latest**` boot 结构配对通过。
- DAC `0.8.0`：Actions 编译、确定性打包、独立 ZIP 校验与下载复核通过。
- 当前安全修复 `c87b3a7694df`：Project contract、DAC `0.8.1` 与 Original/KernelSU/SukiSU/BBG 五机型矩阵 20/20 通过。
- Magisk 公共路径已补为同 SHA Original Artifact 转包；它不执行第二次内核编译，Actions 证据待跑。

## 待完成

BBG 启动链补丁改变公共内核输入，因此此前内核 Artifact 仅作历史证据。当前安全修复 SHA 的矩阵已重跑；仍需 Magisk 同 SHA 转包、代表 Artifact 内容复核、ROM 结构配对和精确 SHA 可复现检查。

这些结果仍不证明启动、硬件兼容、性能、温控、功耗、电池学习、Root 隐藏、BBG 实机保护、刷写或长期稳定。
