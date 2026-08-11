# 温控

内核保留 thermal core、thermal zone、TSENS、BCL、LMH/DCVS、CPU isolate 与 cooling device。删除的仅是 Xiaomi `thermal_message` 用户态邮箱。

DAC 只读取 ROM/设备提供的 thermal headroom；不得抬高 trip、禁用 cooling、屏蔽传感器或覆盖 BCL/LMH。热紧急状态立即撤销性能请求，恢复必须经过连续样本和逐级滞回。

实机门禁覆盖持续 CPU/GPU、游戏、充电、低电量、高环境温度、屏幕开关和重启后的保护恢复。
