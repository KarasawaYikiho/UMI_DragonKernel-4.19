# Freezer

使用现有 Binder freezer + cgroup freezer，不新增冻结驱动，不用 SIGSTOP/SIGCONT 作为生产方案。

```text
ACTIVE -> BACKGROUND -> CACHED -> FREEZE_DELAY -> ELIGIBILITY_CHECK
       -> BINDER_PREPARE -> FREEZING -> FROZEN -> THAWING -> ACTIVE
```

- 粒度：UID/app process cgroup，不冻结任意单线程。
- backend：优先运行时实际 Android/v2 层级，v1 legacy 仅兼容。
- 冻结前：cached、不可见、无关键 FGS/音频/相机/导航/电话/传输；检查 Binder pending transaction。
- 解冻：Binder → cgroup → task profile → 可选短交互请求。
- 冻结与 reclaim 分离；不在 freeze 后立即回收全部内存。
- system_server、zygote、SurfaceFlinger、SystemUI、桌面关键链、输入法、核心媒体/网络/存储/电话/更新/thermal/power/DAC 永不冻结。
- 指标：次数、持续时间、失败、Binder block、thaw latency、CPU/wakeup 减少、swapin 与恢复 jank。

完整功能矩阵通过前默认 dry-run，误冻或 backend 失败立即禁用 freezer 并解冻全部 DAC owner。

## 当前实现

- 严格状态机已实现并覆盖正常 freeze/thaw 链与冻结前回退；非法跨状态转换会被拒绝。
- daemon 只读探测 Binder frozen-info ioctl；诊断脚本同时读取 framework CachedAppOptimizer 开关与 cgroup freezer 能力。
- Android framework owner 可用时不建立第二个 freezer。DAC fallback 尚未接入进程资格信息，默认关闭且不执行冻结。
