# ArtCraft 独立技能

`artcraft-use` 的公开入口已在干净复制目录中验证：不依赖全局 Node 或兄弟仓库，安装锁定 Node、ArtCraft 运行时、四个独立技能源快照及四个官方 CLI，生成 Logo、海报、动态图形片头和带字幕、音频的短片，保留四种原生工程。

当前为开发版。版本 0 与版本 1 的默认在线安装和受控 Codex 技能执行均已通过；版本 1 增加共享预算和有界 Logo 返工。桌面 GUI、其他宿主、完整创作与正式市场验收仍未完成。

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

14 项技能/安装测试通过，含完整隔离首次安装和四原生工程交付；ArtCraft 运行时串行完整 59 项回归通过。`review_ready` 是技术就绪状态。付费账单核销、创作最终评审、故障接管、最终打包和宿主发布仍待完成。

规范事实源：[ArtCraft OpenSpec](https://github.com/full-aigc-plugins/artcraft-plugin/tree/main/openspec/changes/establish-v1-plugin)。

[English](README.md)

开发版本 `0.1.0-dev.1` 增加原子共享预算准入和独立包版本。参见[预算架构](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/ArtCraft-Budget-Architecture.zh_CN.md)。版本 0 的默认在线首次使用及受控 Codex 安装已通过；版本 1 的证据单独记录。

版本 1 在线证据：[首次使用与有界 Logo 返工](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v1.json)、[Codex 安装入口](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/codex-installation-v1.json)。两个修订均交付原生工程，旧工程摘要和音频不变，重跑去重，第三个修订因轮次上限被拒绝。

开发版本 `0.1.0-dev.3` 接通公开原生源工程修订；四领域真实修订和 59 项串行运行时测试通过，并行 EffectCraft 测试偶发失败仍待解决。[架构](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/ArtCraft-Runtime-Architecture.zh_CN.md)。

[版本 3 默认在线首次安装及原生 Logo 修订证据](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v3.json)。使用 dev.3；dev.2 因运行时自报版本不匹配被安装器拒绝，已注明不可使用。

开发版本 `0.1.0-dev.4` 固定四领域技能源 dev.1：修复 CLI 安装/复用的非阻塞锁竞争，改为有界等待。此前并行失败已稳定复现并消除；16 个 EffectCraft 并行样本与 59 项并行原生回归通过。
