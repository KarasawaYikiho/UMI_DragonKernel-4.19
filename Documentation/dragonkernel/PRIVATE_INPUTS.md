# 私有输入规则

私有输入的身份、路径、版本、来源、名称、地址、文件清单、大小、摘要、归档结构、元数据、图像、日志、镜像、密钥和签名材料不得进入 Git、提交信息、Issue、PR、Actions、缓存、Artifact 或 Release。

公开文档只使用以下引用：

- `umi`、`cmi`、`cas`：`Hyper3`
- `thyme`、`apollo`：`Lineage_**Latest**`
- `Lineage_**Latest**` 包与对应镜像目录必须解析为同一 boot；`thyme` 与 `apollo` 各保留一个档案

## 本地命令

```bash
scripts/dragonkernel/prepare_rom_boot.sh <private-input> <device>
scripts/dragonkernel/validate_rom_artifact.sh <device> <artifact-dir> <output-boot.img>
scripts/dragonkernel/validate_magisk_artifact.sh <device> <original-artifact-dir> <output-boot.img>
```

- 输入和输出只能位于仓库外或被 Git 忽略的目录。
- 脚本只能输出通用成功/失败结果，不打印私有身份或内容。
- 每个 ROM 档案只用于其来源设备；不得跨型号复用。
- CI 只处理公开源码产物；正式 ROM 刷写包必须等待安全的非公开注入流程与实机门禁。
- Magisk 模板由目标设备使用 Magisk App 修补自身 ROM 镜像；本地只替换 Original 内核并验证 ramdisk 保持。
