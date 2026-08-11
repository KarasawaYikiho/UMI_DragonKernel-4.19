# 基线指标

当前只有源码、构建与结构证据；没有实机数据时不填写功耗、帧率、温度或延迟数字。

| 场景 | 固定条件 | 指标 | 通过原则 |
|---|---|---|---|
| 日常 | 固定亮度、网络、电量区间、环境温度；10 分钟桌面/设置/浏览/切换/空闲混合 | battery-side W/Wh、frame P50/P95/P99、jank、CPU/GPU/DDR/idle residency | 约 2 W 是软目标；P95/P99 和可见流畅优先 |
| 桌面/超级岛 | 同一设备、ROM、刷新率与事件脚本 | frame P95/P99、launch/switch latency、prime residency、boost tail | 不允许包名内核特判；两场景均不得回退 |
| 游戏 | 当前实际最高开放帧率；20–30 分钟 | avg/1%/0.1% low、frame P95/P99、W、温度、throttle、residency | 先稳定目标帧，再降低多余资源 |
| 后台 | 统一 app 状态与恢复步骤 | freeze 成功率、CPU time、wakeups、thaw latency、Binder block、swapin jank | 正确语义优先，不误冻关键服务 |
| 待机 | 固定网络、通知/电话/闹钟矩阵 | wakeups、deep idle、耗电、消息时延 | 不破坏通知、电话、闹钟、网络 |
| 温控 | 固定负载、环境与充电状态 | thermal state、headroom、频率/帧时间振荡、峰值/持续值 | 不绕过 cooling；持续表现优先 |

每次 A/B 只改变一个独立策略，记录 commit、配置、样本时长、原始证据位置、回滚结果。实机阶段开始前本文件保持“无数值基线”。
