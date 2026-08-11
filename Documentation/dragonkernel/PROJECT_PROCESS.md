# 执行流程

## O：优化完成门禁

1. 冻结调度：WALT、schedutil、UCLAMP、Binder、boost、迁移、RT 饥饿和温控降频交互。
2. 冻结内存与 I/O：PSI、回收、zram、BFQ/WBT、F2FS、写回和前后台压力。
3. 冻结温控与充电：删除 `thermal_message` 后，确认 thermal zone、TSENS、BCL、LMH、冷却设备和硬件保护完整；禁止抬高或绕过安全限制。
4. 冻结用户态策略：审计 Joyose、Power HAL、task profile 与 `msm_performance` 的调度所有权；统一模块隔离远程云控、保留必要本地兼容并由 DAC 仲裁写入。
5. 冻结电池解容：启动容量按机型；仅保留自动学习到的高容量；手动写入仍受原厂值限制；电气、认证和温度保护不变。
6. 冻结 ROM 结构：`Hyper3` 覆盖 `umi`/`cmi`/`cas`；`Lineage_**Latest**` 覆盖 `thyme`/`apollo`；包与镜像目录必须解析为同一 boot。
7. 冻结防格机：Baseband-guard 是所有 Original/Root 变体共享的 LSM 功能，不得成为变体或依赖 KernelSU/SUSFS；另跑五机型功能矩阵。
8. 冻结构建：优先 GitHub Actions 和下载 Artifact；每次源码改动通过 Project contract、受影响快速任务、完整五机型矩阵、产物复核和同 SHA 复现。
9. 清理非必要缓存，仅保留 `main`、干净工作树、必要文档和可复用构建缓存。

Gate O 未全部通过时，禁止刷写、启动、跑分、电池学习或其他实机验证。

## D：实机验证

1. 最终 Original 先验证安全启动、回滚和五机型硬件矩阵。
2. 固定设备、ROM、温度、电量和负载，执行系统桌面与澎湃超级岛 A/B。内核禁止按包名或进程名添加特判。
3. 验证启动容量、扩容学习/FCC、持久化、充放电和全部保护。
4. Original 通过后依次验证 KernelSU、SukiSU、Magisk 的 Root、管理器/注入和应用检测隐藏。
5. 在 Original、Magisk、KernelSU、SukiSU 路径分别验证 Baseband-guard 拒绝非授权关键分区写入，同时不阻断正常更新和 Recovery/Fastboot 恢复。
6. 验证候选 ZIP、Recovery/Fastboot 刷写与回滚。

任何功能、性能、温度、功耗或稳定性回退都返回 O 阶段。

## R：发布

全部实机门禁通过后，CI 从干净提交重新构建、打包、哈希并发布：

- 时区：`Asia/Shanghai`
- Tag：`UMI_<yyyyMMddHHmm>_<Variant>`
- Asset：`UMI_<yyyyMMddHHmm>_<Variant>_Build.zip`
- Module：`UMI_<yyyyMMddHHmm>_DAC_Module_Build.zip`，与镜像使用同一时间戳
- Variant：`Original`、`Magisk`、`KernelSU`、`SukiSU_KPM_SUSFS`

构建或结构验证通过不能替代实机证据。
