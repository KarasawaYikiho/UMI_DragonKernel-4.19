# 游戏控制器

`GAME_DYNAMIC` 是闭环控制器，不是锁频 profile。

- 输入：实际目标帧时间、frame P95/P99、关键线程 util、GPU busy/frequency、DDR 压力、thermal headroom。
- 分类：CPU bound、GPU bound、memory/DDR bound、thermal bound；只先提高瓶颈资源。
- 输出：关键线程 uclamp、bounded core_ctl、KGSL floor、DAC 自有 DDR vote、合格后台 freezer。
- 状态：GAME_LOADING → GAME → GAME_FRAME_RESCUE 或 GAME_THERMAL。
- 稳定目标帧后逐项降低 CPU、GPU、DDR 余量；每步带 hysteresis、cooldown、known-good 与 rollback。
- loading 的 CPU/IO/DDR 请求在进入 GAME 后释放；不得整局保持加载 boost。

当前纯策略核心从运行时目标帧时间判断 P95 违约，连续违约后按 CPU/GPU/内存压力最大项给出归一化 rescue 请求；连续恢复后逐步撤销。thermal limited 立即清空 rescue 并交给温控上限。它尚未连接任何 sysfs/cgroup 写后端，因此只提供分类、迟滞和回滚语义。

最低 Release Gate 是当前 ROM/设备/游戏实际开放的最高帧率，持续 20–30 分钟。禁止写死 120 FPS、GPU 最大频率、DDR max 或全核常驻。
