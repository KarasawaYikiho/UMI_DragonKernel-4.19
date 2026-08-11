# 仓库机制审计

基线：`08f410eb5242`。本阶段只确认机制、接口与控制权，不修改频率、电压、温控阈值、WALT 窗口、GPU pwrlevel 或内存参数。

| 子系统 | 源码与配置 | 运行时接口 | 当前控制者 | 交互、风险与设备依赖 |
|---|---|---|---|---|
| WALT | `kernel/sched/walt.c`、`walt.h`；`CONFIG_SCHED_WALT=y` | `/proc/sys/kernel/sched_*`、sched/WALT tracepoints | 内核 + ROM 调度策略 | 与 SchedTune、uclamp、schedutil、RTG、boost 共用 util；禁止按场景改全局窗口 |
| SchedTune | `kernel/sched/tune.c`；`CONFIG_SCHED_TUNE=y` | schedtune cgroup 的 `boost`、`prefer_idle`、`colocate` | ROM task profiles/Power HAL | DAC 接管前必须识别原 owner，禁止双方反复覆写 |
| uclamp | `kernel/sched/core.c`、`cpufreq_schedutil.c`；`CONFIG_UCLAMP_TASK{,_GROUP}=y` | `sched_setattr`、`cpu.uclamp.min/max`、全局 sysctl | Android task profile + DAC 候选 | 已进入 WALT/schedutil frequency util；错误 floor 会增加驻留与功耗 |
| schedutil | `kernel/sched/cpufreq_schedutil.c`；`CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y` | policy governor 节点；up/down rate、hispeed、PL | cpufreq governor + ROM | 与 WALT、IO-wait、SchedTune、uclamp 同时作用；先测 tail 再改 |
| scheduler boost | `kernel/sched/boost.c` | `/proc/sys/kernel/sched_boost` | 多调用者 refcount | 只能由统一 arbiter 短时请求；热隔离优先 |
| input/CPU boost | `drivers/cpufreq/cpu-boost.c`；`CONFIG_CPU_BOOST=y` | `/sys/devices/system/cpu/cpu_boost/*` | vendor input handler | 当前已修复启停配对；需测重复 boost、尾长和 false activation |
| core_ctl | `kernel/sched/core_ctl.c`；`CONFIG_SCHED_CORE_CTL=y` | cluster `core_ctl/{min_cpus,max_cpus,offline_delay_ms,busy_*,task_thres,...}` | Qualcomm core_ctl | 运行时按 topology/capacity 探测；QTI thermal isolate 高于 DAC |
| QCOM cpufreq-hw | `drivers/cpufreq/qcom-cpufreq-hw.c`；Kona DTS `qcom,cpufreq-hw-epss` | cpufreq policy、available/current frequency、stats | EPSS + cpufreq core | 频表与 cluster 均从运行时/DTS读取，不硬编码 0-3/4-6/7 |
| msm_performance | `drivers/soc/qcom/msm_performance.c`；`CONFIG_MSM_PERFORMANCE=y` | 模块/用户态性能接口 | vendor performance service | 可能与 Joyose/Power HAL/DAC竞争，必须记录 owner |
| KGSL | `drivers/gpu/msm/kgsl_pwrscale.c`、`kgsl_pwrctrl.c`、`adreno.c`；`CONFIG_QCOM_KGSL=y` | KGSL devfreq、governor、busy、pwrlevel、频表 | KGSL governor + thermal + vendor hints | 不锁频；DAC 只管理自己的有界 floor，并保留 known-good 回滚 |
| DDR/LLCC | `drivers/devfreq/{bimc-bwmon,arm-memlat-mon,governor_*}.c`；BWMON/MEMLAT/DEVFREQ configs | devfreq frequency、governor、residency/统计（以真机节点为准） | bwmon/memlat/固件 voter | Kona 是 legacy Qualcomm devfreq 路径；不能假设新式通用 interconnect ABI |
| NoC/msm-bus | Kona DTS `qcom,msm-bus`、RSC、各 client vote | msm-bus/devfreq/debug 接口（需真机确认） | 各硬件 client | DAC 只能新增/释放自己的 vote，不能覆盖显示、相机、UFS、modem client |
| thermal core | `drivers/thermal/thermal_core.c`、`cpu_cooling.c`；`CONFIG_THERMAL=y` | thermal zones、cooling devices、trip/policy 只读审计 | thermal framework/userspace | 已删除 `thermal_message` 邮箱；标准保护链必须保留 |
| TSENS/LMH/DCVS | `drivers/thermal/qcom/{tsens*,lmh*,msm_lmh_dcvs}.c`；TSENS/DCVS configs | zone/cooling/debug 接口 | QTI thermal/firmware | 只作为 DAC 安全输入；不提高阈值、不禁用 cooling |
| BCL/CPU isolate | `drivers/thermal/qcom/{bcl_pmic5,bcl_soc,cpu_isolate}.c`；BCL/isolate configs | cooling device、BCL 状态 | QTI safety | 电流/电压与热隔离绝对优先于性能请求 |
| memcg/reclaim | `mm/memcontrol.c`、`vmscan.c`、`page_alloc.c`；`CONFIG_MEMCG{,_SWAP}=y` | memcg、`/proc/vmstat`、meminfo | kernel + LMKD | 先测 allocstall/refault/direct reclaim，不关闭 reclaim |
| zRAM/swap | `drivers/block/zram/zram_drv.c`；`CONFIG_ZRAM=y` | zram disksize、algorithm、mm_stat、swap stats | init/ROM | 容量与算法属于运行时 ROM 策略；不能只以后台数量判断收益 |
| PSI | `kernel/sched/psi.c`；`CONFIG_PSI=y` | `/proc/pressure/{cpu,memory,io}`、trigger | kernel/LMKD/DAC reader | cmdline 有 `cgroup_disable=pressure`；global/per-cgroup 可用性必须实机确认 |
| LMKD interface | `CONFIG_HAVE_USERSPACE_LOW_MEMORY_KILLER=y`；memcg/PSI ABI | Android properties、PSI/memcg | userspace LMKD | 不引入内核 LMK；freezer 与 kill 分层协作 |
| cgroups/freezer | `kernel/cgroup/{freezer,legacy_freezer}.c`；`CONFIG_CGROUP_FREEZER=y` | v2 `cgroup.freeze/events` 或 v1 `freezer.state` | Android framework + DAC 候选 | 层级需真机探测；按 UID/process cgroup，不冻结单线程 |
| Binder freezer | `drivers/android/binder.c`、UAPI binder header | `BINDER_FREEZE`、`BINDER_GET_FROZEN_INFO` | Android framework | 冻结前检查同步/异步事务，失败必须安全解冻 |
| BFQ | `block/bfq-*.c`；BFQ/group configs | block scheduler 与 blkcg 节点 | block layer/ROM | 按实际块设备确认是否激活，不仅看 Kconfig |
| WBT | `block/blk-wbt.c`；`CONFIG_BLK_WBT{,_SQ}=y` | queue WBT latency/enable 节点 | block layer | 与 BFQ、F2FS、UFS共同影响 tail latency |
| F2FS | `fs/f2fs/`；`CONFIG_F2FS_FS=y` | `/sys/fs/f2fs/*`、iostat、GC/discard stats | F2FS + vold/ROM | 不凭空改 GC/写回；需区分 userdata 实际挂载参数 |
| UFS | `drivers/scsi/ufs/{ufshcd,ufs-qcom,ufs-sysfs}.c`；QCOM UFS configs | runtime/system PM level、link/device state、auto-hibern8 | UFS core/QCOM driver | GAME_LOADING 结束即释放；长期禁用省电状态不可接受 |
| cpuidle/nohz | `drivers/cpuidle/`、`kernel/time/`；CPU_IDLE/ARM_CPUIDLE/NO_HZ/RCU_FAST_NO_HZ | per-CPU state usage/time/residency | cpuidle + firmware | 以深 idle 驻留与唤醒源证明收益 |
| wakeup sources | `drivers/base/power/{wakeup,wakeup_stats}.c`；`CONFIG_PM_WAKELOCKS=y` | wakeup class/debugfs 的 count/time | 各驱动/Android | 不删除 wakelock API；先定位高频 owner |
| IRQ affinity | generic IRQ + 各 vendor driver；Wi-Fi 有自身 HIF affinity 管理 | `/proc/interrupts`、effective affinity | irqbalance/vendor drivers | 不能统一压 CPU0，也不能覆盖 Wi-Fi/display/modem 专用策略 |
| touchscreen | `drivers/input/touchscreen/xiaomi/xiaomi_touch.c` + 各机型 IC；设备 config | Xiaomi touch mode/device attrs、input events | touch HAL/Joyose/游戏工具 | 机型 IC 不同；DAC 只消费交互事件，禁止内核包名特判 |
| display | `drivers/gpu/drm/msm/disp/dpu1/`、DSI/panel DTS | DRM/display/refresh/trace 接口 | SurfaceFlinger/display HAL/DPU | DAC 读取屏幕与目标帧；不接管动态刷新或固定显示带宽 vote |
| BBG | `drivers/baseband-guard` + common config；`CONFIG_BBG=y` | LSM policy | kernel security | 所有变体共享的防格机功能，与性能和 ROOT 路径解耦 |
| fuel gauge 解容 | QCOM/MI fuel-gauge drivers + 机型 DTS | power_supply capacity/FCC/learning | fuel gauge | 启动原厂容量随型号；只解除自动学习上限，不伪造容量或安全参数 |

## 结论

- 现有内核机制足以支撑 DAC 的第一阶段；当前没有证据支持新增 CPU/GPU governor、回移植 MGLRU 或改 OPP。
- 策略冲突的核心不是缺少 knob，而是 Power HAL、Joyose、task profile、msm_performance、boost 与后续 DAC 的所有权未统一。
- Joyose 云控属于 ROM 用户态控制面。内核不得识别其包名；统一模块负责隔离远程配置、保留必要本地服务并把调度写入交给 DAC 仲裁。
- 运行时节点、owner、默认值和机型差异由下一阶段只读采集确认。
