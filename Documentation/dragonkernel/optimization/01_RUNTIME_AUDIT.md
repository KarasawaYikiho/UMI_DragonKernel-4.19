# 运行时审计

采集器：`scripts/dragonkernel/diagnostics/capture_runtime.py`。

覆盖 CPU 拓扑/频率/idle/core_ctl、KGSL/devfreq、thermal/cooling、充电与 fuel-gauge 学习、PSI/zRAM/LMKD/freezer、存储/UFS、IRQ/唤醒源、task profile/cgroup owner、前台窗口、SurfaceFlinger、Power/Thermal HAL、Joyose、DAC 心跳/熔断与 BBG 状态。

```bash
python scripts/dragonkernel/diagnostics/capture_runtime.py --self-test
python scripts/dragonkernel/diagnostics/capture_runtime.py --device <serial>
python scripts/dragonkernel/diagnostics/capture_runtime.py --device <serial> --su
```

采集只读；原始输出必须留在忽略的私有目录。当前无可用 ADB 设备，所有运行时值仍为未知。Gate O 完成前不得开始设备采集或 A/B。
