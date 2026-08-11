# 执行流程

## O：优化冻结

1. 冻结调度、内存/I/O、温控、充电、电池学习、Joyose/DAC 所有权与 ROM 结构。
2. Baseband-guard 保持所有变体共享、Root 无关；启动链与基带关键分区默认拒绝 Root 脚本写入。
3. 用 Actions 完成 Project、DAC、四组五机型内核矩阵、五机型 Magisk 同 SHA 转包、Artifact 内容、ROM 配对与精确 SHA 可复现验证。
4. 清理非必要缓存，只保留 `main` 和干净工作树。

Gate O 完成前禁止刷写、启动、跑分、电池学习或其他实机验证。

## D：实机验证

1. 最终 Original：启动、回滚、硬件、充电、待机和重启。
2. 固定设备、ROM、温度、电量和负载，执行系统桌面与澎湃超级岛 A/B；内核不得添加软件名称特判。
3. 验证模型启动容量、扩展 FCC 学习、持久化与全部电气/认证/温度保护。
4. 依次验证 KernelSU、SukiSU、Magisk 的 Root、管理器/注入和应用检测隐藏。
5. 在四条变体路径复核 BBG 写保护、正常更新及 Recovery/Fastboot 恢复。

任何关键回退都返回 O 阶段，并使旧 SHA 证据失效。

## S：安全与冲突审查

冻结最终 SHA 后运行全仓多轮安全扫描、最终差异扫描、供应链复核、跨 owner/变体/ROM 冲突矩阵和 Release preflight。Critical/High 必须清零；Medium 必须逐项修复或有明确接受记录。

## R：发布

仅 CI 从干净最终 SHA 重建、打包、哈希并发布：

- Tag：`UMI_<yyyyMMddHHmm>_<Variant>`，时区 `Asia/Shanghai`
- Image：`UMI_<yyyyMMddHHmm>_<Variant>_Build.zip`
- Module：`UMI_<yyyyMMddHHmm>_DAC_Module_Build.zip`
- Variant：`Original`、`Magisk`、`KernelSU`、`SukiSU_KPM_SUSFS`
