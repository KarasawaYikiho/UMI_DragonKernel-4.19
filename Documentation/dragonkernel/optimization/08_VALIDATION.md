# 验证门禁

## 源码与产物

1. Project contract 与脚本自检。
2. DAC host/Android AArch64 编译、确定性 ZIP 和独立内容校验。
3. Original、KernelSU、SukiSU、独立 BBG 五机型矩阵。
4. Magisk 五机型候选包必须复用同 SHA Original Artifact，并证明 ZIP 内 Image 完全一致。
5. 代表 Artifact 的外层/内部 SHA、配置、Image magic、对象和日志检查。
6. 五机型 ROM boot 结构配对与同 SHA 可复现检查。

## 实机

Gate O 后先 Original，再 Root 变体。覆盖启动/回滚、硬件、桌面/超级岛 A/B、温控/充电、电池学习、待机、DAC 云控隔离、Root 隐藏、BBG 和 Recovery/Fastboot。

任何源码修复都会使旧 SHA 的构建、结构、安全和实机证据失效。正式结论必须绑定同一最终 SHA。
