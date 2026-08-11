# Dragon Adaptive Controller

DAC 是可选的 Root 管理器可刷模块，不是内核变体。内核提供机制；DAC 负责事件、所有权、仲裁、回滚和 Joyose 远程云控隔离。

## 约束

- 默认禁用性能写入并启用 dry-run。
- 只操作已探测、已移交且可回读的资源。
- thermal/BCL/LMH 优先于任何性能请求。
- Joyose 必须同时匹配 Android system app ID、精确 cmdline 与独占 cgroup；不阻断共享 UID。
- cgroup BPF link 与守护进程生命周期绑定；异常退出自动释放。
- `/dev` 心跳、30 秒监督、90 秒超时和每次启动三次短失败熔断防止假活与重启风暴。

当前版本 `0.8.1`。CPU/freezer/game/thermal 写后端保持禁用，直到设备证据证明 owner、接口、回读和回滚路径。
