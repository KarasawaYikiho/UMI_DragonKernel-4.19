# 运行时审计

本文件定义采集契约，不记录尚未取得的真机值。采集只读，不写 sysfs/procfs，不开始性能 A/B。

| 领域 | 必采证据 | 当前状态 |
|---|---|---|
| 身份 | kernel release、cmdline、设备代号、ROM 公共标签 | 待优化完成后采集 |
| cgroup | mounts、controllers、task profiles、cpuset、schedtune、uclamp、freezer v1/v2 | 待采集 |
| CPU | topology/capacity、policy、governor、频表、time-in-state、idle、core_ctl、boost | 待采集 |
| GPU/DDR | KGSL governor/busy/pwrlevel、devfreq、bwmon/memlat、vote/residency | 待采集 |
| 内存 | meminfo、vmstat、zRAM/swap、global/per-cgroup PSI、LMKD properties | 待采集 |
| 温控 | zones、trips、cooling devices、TSENS/BCL/LMH/DCVS 状态 | 待采集 |
| I/O | block scheduler、BFQ/WBT、F2FS mounts/iostat、UFS PM/link/hibern8 | 待采集 |
| IRQ/待机 | interrupts/affinity、wakeup sources、suspend/idle residency | 待采集 |
| Android | Power HAL/ADPF hints、前台状态、Binder freezer、SurfaceFlinger frame data | 待采集 |
| Xiaomi 控制面 | Joyose、本地性能服务、云配置来源、调度/touch/game/thermal 写入目标与频率 | 待采集 |

## Joyose 云控边界

目标不是粗暴删除 Joyose 进程，而是区分并验证：

1. 远程配置下载、签名/版本缓存与动态下发；
2. 本地游戏识别、触控、Power HAL/性能提示等兼容职责；
3. 对 schedtune、uclamp、cpuset、core_ctl、cpu_boost、KGSL/devfreq 的实际写入；
4. 系统桌面、澎湃超级岛、相机、音频和游戏对其本地能力的依赖。

模块默认阻断第 1 类并记录第 3 类；只有 DAC 已接管且具备回滚时才替代相应写入。任何方案不得停用标准 thermal、BCL、LMH、充电或 modem 安全链。

## 输出

- `runtime.json`：机器可读，包含 capability、path、value、owner_hint、read_error。
- `runtime.md`：只汇总能力存在性和待解决冲突，不泄露私有 ROM 身份。
- 原始数据只进入本地忽略目录；公开证据仅保留脱敏后的能力结论。
