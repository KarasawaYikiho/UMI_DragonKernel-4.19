# 机制审计

| 域 | 保留机制 | 所有权与限制 |
|---|---|---|
| CPU 调度 | WALT、SchedTune、uclamp、schedutil、core_ctl、CPU boost | ROM/Power HAL 保持默认 owner；DAC 只操作明确移交的资源 |
| GPU/DDR/NoC | KGSL、devfreq、bwmon/memlat、msm-bus | 不锁频；只允许有界、可恢复、自有 vote |
| 内存 | memcg、PSI、LMKD、zRAM、reclaim | 不引入内核 LMK，不猜固定容量或算法 |
| Freezer | Android CachedAppOptimizer、cgroup freezer、Binder freeze | Framework 优先；DAC fallback 默认禁用 |
| 存储 | BFQ、WBT、F2FS、UFS 省电状态 | 先测 tail latency；禁止永久关闭省电或改 GC 参数 |
| 温控 | thermal core、TSENS、BCL、LMH、DCVS、cooling device | 安全链优先，不抬阈值、不禁冷却 |
| 电池 | FG 学习、充电 voter、认证、温度/电压/电流保护 | 只解除自动学习上限；启动值和手动上限仍按型号 |
| 云控 | 删除 `thermal_message`；DAC 隔离 Joyose 远程网络 | 不停包、不停组件、不阻断共享 UID；精确进程+cgroup |
| 防格机 | Baseband-guard LSM | 所有变体共享；Root 无关；Recovery/Fastboot 保留恢复能力 |
| Root | Magisk、KernelSU、SukiSU + KPM + SUSFS | 只作为变体；隐藏需覆盖内核、管理器/注入、应用检测 |

优化以机制、所有权、回滚和测量为准。频率、电压、温控阈值、容量、CPU mask、包名和进程名不得凭经验硬编码。
