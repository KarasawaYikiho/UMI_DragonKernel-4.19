# DAC 架构

Dragon Adaptive Controller 是可选的事件驱动用户态策略层。内核保留 WALT、schedutil、SchedTune、uclamp、core_ctl、KGSL、devfreq、freezer 与 thermal mechanism；DAC 只统一 policy ownership。

```text
Android events / Power HAL / PSI / thermal / frame data
                         |
                    event loop
                         |
 scene state -> policy -> ownership/arbiter -> probed backend
                         |
  uclamp/cpuset/core_ctl/KGSL/devfreq/freezer (thermal只读)
```

## 必备契约

- 原生 daemon + 小型 CLI；shell 只负责模块安装与启动。
- `epoll`/uevent/inotify/PSI trigger/timerfd；生产 telemetry 仅低频摘要。
- 每个 backend 实现 probe/read/apply/verify/restore/supported。
- dry-run、safe mode、kill switch、原子切换、失败回滚、控制权数据库。
- 不硬编码 CPU mask、sysfs 路径、频率、温度阈值或内核包名。
- critical thermal、kernel safety、system critical semantics 始终高于用户 profile。

## 统一模块

不能安全纳入内核的 DAC、诊断、Joyose 云控隔离和配置放入一个标准 ROOT 管理器模块；Magisk、KernelSU、SukiSU 使用同一 ZIP。模块不是内核变体，也不改变 Original 内核机制。

- 文件名：`UMI_<yyyyMMddHHmm>_DAC_Module_Build.zip`
- 时间戳：与同次镜像 Release 相同，时区 `Asia/Shanghai`
- daemon 不依赖特定 ROOT manager API；安装/启动 wrapper 可识别通用模块环境。
- 性能策略默认关闭并保持 dry-run；Joyose 远端网络隔离独立启用。
- 云控隔离只附加到进程独占的既有 cgroup v2 叶节点，不移动任务；BPF link 绑定 daemon FD 生命周期，共享节点、BPF 不可用或校验失败立即进入 SAFE。
- Recovery 默认不启动；卸载必须解冻全部任务并恢复 DAC 拥有的 knob。

## Xiaomi 云控

静态 ROM 证据确认 Joyose 同时包含远端下发以及调度、游戏/性能、温控和内存策略，并使用共享系统 UID；默认进程还混合远端与本地职责。因此禁止按 UID 断网、删包、停组件或猜测域名。

DAC 扫描 Joyose 进程的既有 cgroup v2 路径，仅在 `cgroup.procs` 全部属于 Joyose 时附加 ingress/egress cgroup BPF 丢包程序。卸载、切换 observe 或失败时只卸载自身程序；Lineage 无该包时无操作。本地 Binder、Unix socket 与策略代码保留，后续写入仍需 DAC 所有权仲裁。
