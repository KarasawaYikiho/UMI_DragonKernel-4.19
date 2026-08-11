# 持续温控策略

标准 thermal zones、TSENS、BCL、LMH/DCVS、CPU isolate、CPU/GPU/devfreq cooling 和硬件保护全部保留。DAC 只读取状态并降低非关键请求，不写 trip point，不提供 Thermal Off。

状态为 NORMAL、WARM、HOT、CRITICAL，切换必须有移动平均、进入/退出迟滞和最小驻留时间。优先处理顺序：重复 boost → 后台竞争 → 过量 GPU/DDR/CPU headroom → 保持帧 deadline 所需资源。

Joyose 远程温控配置属于要隔离的云控面，但隔离不得删除标准 QTI/Android thermal service 能力。所有阈值来自 DTS、vendor thermal 配置或运行时读取，不采用网络经验值。

当前纯策略核心只接收外部提供的 headroom、进入/退出阈值、恢复驻留时间和归一化 cap。升温立即收紧 DAC 请求，恢复逐级且满足迟滞与驻留时间；它不创建阈值，也不写 thermal 节点。日常软功耗预算同样不写死容量或功率，只有连续超预算才收紧，出现延迟回退立即放宽。

目标是 20–30 分钟稳定表现与小幅 thermal headroom，不是前五分钟峰值。Phase 0–6 不修改 OPP、电压或 thermal trip。
