# CPU 策略

优先级：cpuset → uclamp → SchedTune compatibility → bounded core_ctl → schedutil exposed parameters → 最后才考虑小型内核补丁。

## 当前约束

- 保留 WALT；现有 uclamp 已参与 WALT/schedutil frequency util。
- BoostArbiter 合并 vendor input、交互、启动、游戏加载、frame rescue 与 thermal override。
- topology/capacity、policy 和 core_ctl cluster 均运行时读取。
- Joyose、Power HAL、msm_performance 或 ROM task profile 持有的 knob 在明确交接前只记录不覆盖。

## 实施顺序

1. 采集 owner、boost duration/tail、prime residency、core_ctl false activation。
2. DAC dry-run 重放交互、启动、桌面和超级岛事件。
3. 仅接管可完整恢复的 uclamp/cpuset 请求。
4. 去除重复 boost，再评估 core_ctl 与 schedutil 小步调整。
5. 任何改动跑桌面、超级岛、启动、切换、下载、视频、相机、游戏和 screen-off 回归。

禁止新增 governor、固定长全核 boost、全前台绑 prime、按应用名修改 scheduler 或修改 OPP/电压。

## 当前实现

`BoostArbiter` 已建立按 owner 的有期 uclamp 请求模型：相同 owner 续期，不同 owner 取最大有效 floor，thermal cap 始终优先，释放只影响自身请求。CPU backend 默认关闭，当前不写 cgroup、uclamp、cpuset、core_ctl 或 boost 节点。
