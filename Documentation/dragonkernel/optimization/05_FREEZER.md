# Freezer

Android CachedAppOptimizer 是首选 owner。DAC 仅保留默认禁用的 fallback 状态机：`ACTIVE -> FREEZE_REQUESTED -> FROZEN -> THAW_REQUESTED -> ACTIVE`。

冻结前必须确认目标资格、cgroup 所有权和 Binder 同步/异步事务状态；失败或超时必须安全解冻。禁止按单线程冻结、禁止接管前台/可见/音频/下载/导航/系统关键进程，禁止与 Framework 双重写入。

当前只做能力探测和状态机自检，不写 freezer 接口。
