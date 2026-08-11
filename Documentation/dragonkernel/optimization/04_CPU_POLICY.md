# CPU 策略

`BoostArbiter` 按 owner 保存短时请求，取有效最高 floor，并由 thermal cap 统一收紧。释放一个 owner 不得清除其他 owner 的请求。

每线程 uclamp 后端只接受明确移交的线程：写入前快照，写后回读，释放时仅在值仍由 DAC 所有时恢复。线程退出视为完成，外部 owner 改值时禁止覆盖；瞬时恢复失败保留记录重试。

禁止修改全局 WALT 窗口、固定频率、CPU mask 或现有 ROM task-profile cgroup。CPU 写入仍为设备阶段后的独立开关。
