# 私有输入规则

以下内容不得进入 Git、提交信息、Issue、PR、公开日志、Actions 缓存、Artifact 元数据或 Release：

- 输入身份、路径、版本、来源、下载地址、名称和可识别标记
- 文件列表、大小、哈希、归档结构、解析元数据、图片和日志
- 原始镜像、密钥、签名材料和个人信息

## 本地 ROM 适配

```bash
scripts/dragonkernel/prepare_rom_boot.sh <private-input> <device>
scripts/dragonkernel/validate_rom_artifact.sh <device> <artifact-dir> <output-boot.img>
```

- 输入保存在仓库外或被忽略目录；路径只通过参数或环境变量传入。
- 脚本只输出通用成功或失败结果，不打印输入身份和内容清单。
- boot 模板、重打包结果和设备日志只用于本地验证，不上传。
- 未建立批准的非公开注入通道前，CI 只能处理公开源码产物，不能生成正式 ROM 刷机包。
