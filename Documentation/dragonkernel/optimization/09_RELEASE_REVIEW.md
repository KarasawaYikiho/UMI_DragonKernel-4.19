# Release 安全与冲突审查

仅在优化和实机门禁完成、最终 SHA 冻结后执行。

## 安全

1. 多轮全仓扫描：内核攻击面、Root 授权/隐藏、DAC、BBG、ROM/AVB/打包和 CI。
2. 最终差异扫描：从已审基线到候选 SHA 的全部变更。
3. 供应链：submodule、补丁、工具链、Action、下载工具与 SHA/版本锁。
4. 机密：私有 ROM、路径、摘要、日志、镜像和密钥不得进入 Git、Actions、Artifact 或 Release。

Critical/High 未清零阻止发布；Medium 必须逐项修复或记录接受理由、owner 和补偿控制。修复后重跑受影响扫描和全部失效证据。

## 冲突

| 交叉面 | 必查项 |
|---|---|
| 调度 owner | WALT/SchedTune/uclamp/schedutil、Power HAL、Joyose、DAC |
| 热与电 | thermal/BCL/LMH、boost、充电 voter、FCC 学习 |
| 内存 | LMKD、PSI、reclaim、zRAM、Framework/DAC freezer |
| Root/LSM | SELinux、BBG、KernelSU、SukiSU/KPM/SUSFS、Magisk |
| 设备/ROM | 五机型 config/DTS、`Hyper3`、`Lineage_**Latest**`、boot/AVB |
| 产物 | 变体命名、Image、模块、AnyKernel3、回滚路径 |

Release preflight 只收集最终 SHA 和冲突范围，不替代上述人工/工具审查或实机证据。
