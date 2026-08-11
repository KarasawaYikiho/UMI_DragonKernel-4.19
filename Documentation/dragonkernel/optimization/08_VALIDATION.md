# 优化验证

## 静态与 CI

1. Project contract：文档、配置契约、脚本语法、自测、命名与私有信息门禁。
2. 受影响内核改动：Original、KernelSU、SukiSU 五机型矩阵；Magisk 使用对应 Original Image 与私有模板做结构验证。
3. BBG：公共 config/object/log 门禁和独立 Root-none 五机型功能矩阵；不得成为变体。
4. 用户态模块：同一源码构建一次，校验 ZIP 结构、权限、hash、可复现性和三类 ROOT 管理器兼容入口。
5. 最终提交：五机型 ROM 结构配对、代表产物解包复核、同 SHA Image/候选 ZIP/模块 ZIP 复现。

## 实机顺序

只有 CPU/调度、freezer、日常功耗、游戏闭环、持续温控、云控隔离、电池、ROM 与构建路径全部冻结后才开始：

1. Original 安全启动、回滚、基础硬件与 24 小时混合稳定；
2. 系统桌面、澎湃超级岛、应用启动/切换、相机、音频、电话、网络、待机 A/B；
3. freezer/LMKD/Binder 功能矩阵与 100 次 freeze/thaw；
4. 日常固定条件功耗与 frame P95/P99；
5. 游戏 20–30 分钟持续帧率、功耗和温控；
6. 电池型号初始容量、扩容学习、持久化与全部保护；
7. Magisk、KernelSU、SukiSU 的 ROOT/隐藏/模块安装；
8. 各路径 BBG 正常更新、关键分区拒写与 Recovery/Fastboot 恢复；
9. 候选 ZIP 刷写、卸载和回滚。

出现 boot/panic/reboot/ANR/Binder/audio/camera/call/alarm/notification/network/suspend/charging/FPS/P99 回归，立即回滚该单项并返回优化阶段。

## 单项 Evidence

每个改变必须记录 Problem、Current implementation、Evidence、Proposed change、Expected benefit、Risk、Compatibility、Rollback、Test plan；没有设备 trace 时不得把理论判断写成性能完成。
