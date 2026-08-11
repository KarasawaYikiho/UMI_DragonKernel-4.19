# 私有输入

禁止提交、上传或公开私有输入的身份、路径、版本、来源、文件清单、大小、摘要、元数据、镜像、日志、密钥或签名材料。

公开引用仅允许：

- `umi`、`cmi`、`cas`：`Hyper3`
- `thyme`、`apollo`：`Lineage_**Latest**`

输入和输出必须位于仓库外或 Git 忽略目录。脚本只能报告通用成功/失败，不得打印私有内容。每个 ROM 档案只用于来源设备。公开 Magisk Action 仅把同 SHA Original Image 打包并证明二进制一致；私有路径必须由目标设备使用 Magisk 修补自身 ROM boot，再仅替换该 Image。

```bash
scripts/dragonkernel/prepare_rom_boot.sh <private-input> <device>
scripts/dragonkernel/validate_rom_artifact.sh <device> <artifact-dir> <output-boot.img>
scripts/dragonkernel/validate_magisk_artifact.sh <device> <original-artifact-dir> <output-boot.img>
```

正式 ROM 刷写包不得进入公开 CI；发布前必须走非公开注入、最终 SHA 校验与实机门禁。
