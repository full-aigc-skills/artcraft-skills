# ArtCraft 独立技能

`artcraft-use` 的公开入口已在干净复制目录中验证：不依赖全局 Node 或兄弟仓库，安装锁定 Node、ArtCraft 运行时、四个独立技能源快照及四个官方 CLI，生成 Logo、海报、动态图形片头和带字幕、音频的短片，保留四种原生工程。

当前为开发版；测试使用本地锁定发布包，四 CLI 从官方来源实际安装。自有发布包的在线下载与插件宿主安装尚未验收，不能把本地验证写成市场可安装。

## 首次使用

需要 macOS arm64、Python 3.11+。从实际加载的技能目录调用 `scripts/workflow.py`，参见[技能入口](skills/artcraft-use/SKILL.md)和[工作流合同](skills/artcraft-use/references/workflow.md)。首次自动安装，后续重新核验复用，不修改 PATH。

```bash
python3 /absolute/skill/artcraft-use/scripts/workflow.py \
  /absolute/skill/artcraft-use/examples/brand-campaign.json \
  --output /absolute/path/project --authorization project-authorized \
  --asset voice=/absolute/path/voice.wav
```

示例需要已有 WAV；不生成伪配音。开发离线验证添加 `--node-archive` 和 `--bundle-dir`；可选 `--native-archive-dir` 指定官方 CLI ZIP 目录。所有离线制品仍强制核验摘要。

## 来源与产物

| 内容 | 事实源 | 安装行为 |
| --- | --- | --- |
| 技能、setup 与项目入口 | 本独立源码包 | 单技能目录可独立复制 |
| ArtCraft 运行时 | artcraft-plugin 的 src、schemas、package.json | 固定 ZIP 摘要与逐文件摘要，原子安装 |
| 四领域技能 | 各自独立 `*-skills` 包 | 固定生成快照，只调用其公开安装和工作流脚本 |
| Node 与四 CLI | 官方固定版本制品 | 二进制、版本、许可与命令能力核验 |

项目保留安装回执、冻结计划、SQLite 账本、结果回执与子工程交付。相同项目入口串行；同修订重跑复用任务，同修订修改内容报冲突。不同修订只重建受影响节点。

## 验证与未完成项

12 项技能/安装测试通过，含完整隔离首次安装和四原生工程交付；ArtCraft 运行时完整 48 项回归通过。`review_ready` 是技术就绪状态。原生源工程局部修订绑定、共享预算、创作最终评审、故障接管、最终打包和宿主发布仍待完成。

规范事实源：[ArtCraft OpenSpec](https://github.com/full-aigc-plugins/artcraft-plugin/tree/main/openspec/changes/establish-v1-plugin)。

[English](README.md)
