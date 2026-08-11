# DAC 架构

Dragon Adaptive Controller 是可选的事件驱动用户态策略层。内核保留 WALT、schedutil、SchedTune、uclamp、core_ctl、KGSL、devfreq、freezer 与 thermal mechanism；DAC 只统一 policy ownership。

```text
Android events / Power HAL / PSI / thermal / frame data
                         |
                    event loop
                         |
 scene state -> policy -> ownership/arbiter -> probed backend
                         |
  uclamp/cpuset/core_ctl/KGSL/devfreq/freezer (thermal只读)
```

## 必备契约

- 原生 daemon + 小型 CLI；shell 只负责模块安装与启动。
- `epoll`/uevent/inotify/PSI trigger/timerfd；生产 telemetry 仅低频摘要。
- 每个 backend 实现 probe/read/apply/verify/restore/supported。
- dry-run、safe mode、kill switch、原子切换、失败回滚、控制权数据库。
- 不硬编码 CPU mask、sysfs 路径、频率、温度阈值或内核包名。
- critical thermal、kernel safety、system critical semantics 始终高于用户 profile。

## 统一模块

不能安全纳入内核的 DAC、诊断、Joyose 云控隔离和配置放入一个标准 ROOT 管理器模块；Magisk、KernelSU、SukiSU 使用同一 ZIP。模块不是内核变体，也不改变 Original 内核机制。

- 文件名：`UMI_<yyyyMMddHHmm>_DAC_Module_Build.zip`
- 时间戳：与同次镜像 Release 相同，时区 `Asia/Shanghai`
- daemon 不依赖特定 ROOT manager API；安装/启动 wrapper 可识别通用模块环境。
- 默认关闭写入，首次启动只 probe/dry-run；配置错误或 crash loop 自动恢复 vendor defaults。
- 未验证的 Joyose block 配置会进入 SAFE；当前阶段只允许 observe。
- Recovery 默认不启动；卸载必须解冻全部任务并恢复 DAC 拥有的 knob。

## Xiaomi 云控

模块对 Joyose 采用“远程云控隔离 + 本地兼容保留 + 写入所有权仲裁”，不以删包/停服务作为默认方案。云配置拦截点必须来自 ROM 运行时审计；未知域名、文件或 property 不得猜测。
