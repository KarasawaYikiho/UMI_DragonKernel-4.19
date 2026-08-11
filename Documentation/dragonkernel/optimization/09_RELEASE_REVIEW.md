# Release 安全与冲突审查

正式 Release 只允许从已完成优化和实机验证的最终 SHA 生成。开放源码不依赖隐蔽实现换取安全；私有 ROM、密钥、签名与未修复漏洞细节仍不得公开。

## 安全门禁

1. 手动运行 `Release security preflight`，以完整 base/candidate SHA 生成 JSON；它拒绝已知危险新增行、私有/Agent/缓存路径和逃逸符号链接，并列出需要人工检查的 owner scope。
2. 对最终仓库执行多轮全量安全扫描，并对候选 SHA 相对上一已知安全基线执行变更扫描；preflight 不能替代这两项审查。
3. 覆盖内核 syscall/ioctl、procfs/sysfs、LSM、Binder、cgroup/BPF、fuel gauge、镜像/ZIP 解析、CI、子模块与 DAC root daemon/安装脚本。
4. Root 变体分别审查权限提升、凭据、hook/KPM/SUSFS、隐藏边界和管理器/注入链；BBG 始终按公共 LSM 单独审查。
5. 所有外部源码、GitHub Action 与预编译工具必须固定提交和来源；Project contract 拒绝可移动 Action 标签与未审查 Action；Release 资产必须可复现并带独立哈希。
6. 禁止未解决的 Critical/High。Medium 必须修复或由维护者逐项记录影响、可达性与补偿控制；Low 不得成批掩盖同一根因。
7. 私有输入、凭据、签名材料、漏洞利用细节和本地路径不得进入 Git、Actions、Artifact、日志或 Release。

## 冲突门禁

| 领域 | 必查冲突 |
|---|---|
| 调度 | WALT、Power HAL、Joyose、本地 task profile、SchedTune、uclamp、boost、core_ctl 与 DAC 的 owner/restore |
| 温控/电池 | thermal、TSENS、BCL、LMH、cooling、充电保护与解容学习；禁止安全阈值被策略覆盖 |
| 内存 | Android CachedAppOptimizer、Binder freezer、cgroup freezer、LMKD、reclaim/zRAM 与 DAC fallback |
| 安全 | BBG 与 Original/Magisk/KernelSU/SukiSU、SUSFS/KPM/LSM hook 顺序及正常更新/恢复 |
| 网络 | Joyose cgroup BPF 与 Android/netd BPF、共享 UID、VPN、Wi-Fi/蜂窝、下载和本地 Binder/Unix socket |
| 打包 | 五机型 boot/AVB/DTBO/ramdisk/module、ROOT 修补、候选 ZIP 与统一 DAC 模块命名/哈希 |

## 通过条件

- 安全发现、冲突项、实机回归、五机型矩阵、ROM 配对和同 SHA 复现均绑定最终提交。
- 任何 owner 不明确、回滚不完整、权限过宽、私有信息泄露或可达高风险发现均阻止发布。
- 修复后必须重跑受影响扫描、Actions、产物复核和必要实机回归；旧证据不得迁移到新 SHA。
