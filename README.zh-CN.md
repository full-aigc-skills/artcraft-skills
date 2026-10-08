# ArtCraft 独立技能

维护分支已修正十个独立技能源的命令使用指南：明确离线查询、单领域调用与 DAG 原生命令交付的入口，清理旧依赖版本说明。16项命令回归及文档／固定索引检查通过；固定source91/plugin119已包含新指南；安装与原生指南实测证据见下文。运行时和领域依赖未变。 [Evidence](docs/evidence/command-guidance-refresh-20261008.json).

固定 source88／plugin116 已通过十项 Art 独立公开冷安装（Node／核心及所选 Vector32）、固定安装副本五节点品牌返工／移动交付和两条真实原生品牌误改阻断。64 安装摘要一致；54 个未变技能沿用历史冷安装证明。完整首版仍开放。[固定证据](docs/evidence/craft-art116-brand-guard-fixed-first-use-20261008.json)。

Vector32 分发升级候选将品牌校验模块纳入受信回执，并接受与锁定 v 标签完全匹配的 ZIP 前缀。暖缓存五节点原生返工与移动交付通过，该候选阶段的固定发行及错误阻断验收待验状态已由上方固定证据更新。[架构](docs/ArtCraft-Brand-Guard-Distribution-Architecture.zh_CN.md)。

固定 source87／plugin115 已包含十个 Art 技能的 Node／组合安装锁修复，每把锁最多等待 120 秒。实际 Codex 安装发现全部 64 个技能，零加载错误；10 个变化技能逐项独立冷安装通过，其余 54 项仅在完整摘要相等时复用历史冷证明。[安装锁架构](docs/ArtCraft-Install-Lock-Architecture.zh_CN.md)。 固定安装副本的四领域原生创建、源返工、同修订复用、回执篡改拒绝及移动包验证通过；前两次磁盘不足失败日志保留。[固定验收](docs/evidence/craft-art115-install-lock-fixed-first-use-20261008.json)。

固定源86／插件114通过10个Art技能独立冷安装、保留工程的四域原生创建／返工／移动交付；64个安装身份一致，完整首版仍未完成。[证据](docs/evidence/craft-art-photo34-fixed-first-use-20261008.json)。[架构](docs/ArtCraft-Photo-Integrity-Dependency-Architecture.zh_CN.md)。
多领域创作需求进入，交付项目清单、工作流记录、四领域子工程引用及验收记录。

当前技能源快照：`0.1.0-dev.94`；已验收插件：`0.1.0-dev.122`；10 个独立技能。

已验证首次使用平台：macOS arm64、Python 3.11+。固定运行时安装在用户数据目录，技能文件保留在宿主加载目录。当前为开发版本；完整首版验收及通用 Skills CLI 实际安装仍未完成。

## 首次使用

在宿主中调用 **`artcraft-use`**。直接使用 CLI 时，将 `SKILL_DIR` 设为宿主实际加载的 `SKILL.md` 所在绝对目录；可能位于用户／项目 `.agents/skills`、插件内部或宿主缓存，以实际路径为准。以下入口在调用前安装并核验固定运行时。

<!-- CRAFT_FIRST_USE_START -->
```bash
: "${SKILL_DIR:?Set to the actual loaded skill directory}"
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- --version
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- --help
```
<!-- CRAFT_FIRST_USE_END -->

实际制作、所需输入、原生工程和局部修改参见[可编辑工作流](skills/artcraft-use/references/workflow.md)。[安装与技能入口](skills/artcraft-use/SKILL.md) · [版本绑定历史](RELEASE-HISTORY.zh-CN.md)。版本与命令查询验证安装和发现，不代表创作完成。 ArtCraft 不适配或调用剪映。

[首次使用入口证据](docs/evidence/craft-readme-first-use-navigation-20261007.json)。

固定安装路径验收：独立技能及 Art 混合工作流在含中文和空格的路径下，通过原生创建与重开、定点返工及导出；Art 另验证移动交付包。技能与运行时身份保持不变。该结果仅覆盖 macOS arm64 的本次首次使用场景。 [路径验收证据](docs/evidence/craft-fixed-unicode-path-first-use-20261007.json).

固定发行前的历史源码候选：结构损坏的 runtime／Node 锁在写运行时目录或下载前返回本地恢复诊断。五项候选原生首次使用通过；发布插件快照保持不变，新不可变发行安装需另行验收。 [锁诊断候选](docs/ArtCraft-Lock-Shape-Architecture.zh_CN.md).

---

Art完整领域命令组件候选已支持2639条离线查询、实际MCP schema及只安装选定领域的公开交接。四域冷安装创建／重开／返工与目标／对照像素通过；固定安装6.50及DAG原生交付6.51仍开放。 [Evidence](docs/evidence/art-complete-domain-component-candidate-20261007.json).

固定原生首次安装与完整命令恢复验收通过：新版五插件58技能逐项独立冷安装，十个Art技能分别安装四领域；四个原生下载半包SSL EOF恢复、72个原生保存后故障、四个健康命令返工及混合HD返工／恢复／移动包通过，全部安装摘要保全。仅关闭领域2.10／8.11与Art4.10；2639条命令逐项、GUI、模型、通用Skills CLI及完整V1仍开放。 [版本及证据](docs/evidence/codex-native-download-first-use-20261007.json).

固定发布前的候选记录：Art原生首用恢复候选固定Film18／Effect、Photo、Vector17，复用runtime78。此前Art80冷安装在领域CLI下载遇到SSL EOF失败，保留失败证据；新固定安装验收仍开放。

历史发行记录：当前独立技能源 dev.54 复用不可变runtime dev.78，固定 Film17 与 Effect／Photo／Vector16 的完整命令内层JSON修复。新固定安装验收进行中；旧证据保持其原版本。

历史发行记录：当前技能源 dev.53／运行时 dev.78，固定 Film16 与 Effect／Photo／Vector15 技能源。恢复模块摘要进入能力快照和可信启动器；固定安装门禁4.9已通过，完整V1仍开放，下方历史证据仍按原版本解读。

固定插件 dev.77／技能源 dev.52／运行时 dev.76 已通过实际安装首用：Codex 发现五插件58项技能、零加载错误；十个 Art 技能分别从空运行时公开安装全部四领域（累计461.66秒）；1080p／24 fps／五秒混合创作、Logo 返工、坏帧恢复及五子工程移动包通过（215.727秒）；四领域公开工作流24个保存后响应故障均停止且不重放。全部58项安装身份、四领域完整源包、原生CLI和Node摘要保全，四项固定提交CI通过。测试检查器曾产生一个字节码缓存，清理后重新核验固定身份并补跑第十项。仅关闭OpenSpec4.7分发升级子门禁；全量2639命令／GUI／修订、通用Skills CLI、模型和完整V1仍开放。测试代理捕获工程不证明产品保留失败暂存工程。[版本绑定证据](docs/evidence/codex-art77-domain-distribution-first-use-20261007.json)。
固定领域客户端首用复验：Film 插件 dev.16／技能源 dev.15，Effect／Photo／Vector 插件 dev.15／技能源 dev.14。隔离 Codex 发现58项零错误；实际安装副本24类保存后故障、四个健康公开工作流和已发布 Art 引擎＋安装后 Vector 客户端六类故障通过，全部58项安装摘要保全。Art dev.75 内置旧领域分发包尚需升级，全量命令／GUI／模型验收仍开放。[版本绑定证据](docs/evidence/codex-public-workflow-session-first-use-20261007.json)。
下载恢复固定发行验收通过：十项技能源均与dev.51逐文件一致，各自空运行时公开安装全部领域；dev.75实际安装副本冷混合／返工／恢复／打包、58项安装摘要与固定标签CI通过。[证据](docs/evidence/codex-art75-download-recovery-first-use-20261007.json)。本次关闭OpenSpec4.8；4.7编排协议故障、独立Skills CLI和完整V1仍开放。

技能源dev.51补充Node与领域技能制品的最多三次只读下载恢复；半包清理及固定摘要仍强制校验。[方案](docs/ArtCraft-Download-Recovery-Architecture.zh_CN.md)，[候选回归](docs/evidence/download-recovery-candidate-20261007.json)。全部十技能冷安装与固定宿主验收保持开放。dev.50仅保留标签，因元数据未更新不发布、不用于插件快照。

领域分发候选已升级至dev.73：四领域固定完整命令／协议修复技能源，公开冷安装混合创作、依赖返工、恢复、移动包和24个领域故障案例通过。[候选证据](docs/evidence/art-domain-distribution-candidate-20261007.json)。新技能源／插件固定安装与十技能完整安装验收另行跟踪。

技能源 `0.1.0-dev.47` 固定 Art runtime `0.1.0-dev.68`、Photo 源 dev.10 与维护版 CLI `0.2.0-craft.1`，Film dev.10、Effect dev.9、Vector dev.10。四领域智能对象候选首次使用通过：在已有海报工程替换内容，保留蒙版、变换和非目标图层，更新依赖任务并复用无关任务。固定插件宿主验收与完整首版仍开放。[架构与证据](docs/ArtCraft-Smart-Mixed-Architecture.zh_CN.md)。

历史固定 JPEG 发行 dev.59／技能源 dev.41／运行时 dev.58：隔离 Codex 发现五插件／58 技能／零错误；安装副本 JPEG、PNG、PCM 原生交付、十项 Art 冷安装及全部安装摘要保全通过。渐进 JPEG 交付重开的三层 Photo 工程及独立解码 PNG／PSD，迁移验包通过。[版本绑定证据](docs/evidence/codex-release59-jpeg-first-use-20261006.json)。完整首版／模型／GUI／创作验收仍开放。

技能源 dev.41 固定 JPEG 运行时 dev.58，安装后宿主复验通过；历史候选证据保留 dev.56 范围。

历史技能源 dev.39／插件 dev.55／runtime dev.54 已通过固定安装后的 PCM WAV 冷启动原生交付与迁移打包；十项 Art 独立冷启动及原安装 58 项技能摘要核对通过。完整首版／模型／GUI／创作及通用 Skills CLI 验收仍开放。

`artcraft-use` 的公开入口已在干净复制目录中验证：不依赖全局 Node 或兄弟仓库，安装锁定 Node、ArtCraft 运行时、四个独立技能源快照及四个锁定原生 CLI，生成 Logo、海报、动态图形片头和带字幕、音频的短片，保留四种原生工程。

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

当前默认技能源测试 79 项：66 通过、13 可选跳过；运行时默认回归 128 项：123 通过、5 可选跳过。固定安装技能的在线首次使用 3 项通过、0 跳过，包含四种原生源工程返工与三类尺寸修改。`review_ready` 是技术就绪状态。付费账单核销、创作最终评审、故障接管、最终创作交付审核和宿主发布仍待完成。

规范事实源：[ArtCraft OpenSpec](https://github.com/full-aigc-plugins/artcraft-plugin/tree/main/openspec/changes/establish-v1-plugin)。

[English](README.md)

开发版本 `0.1.0-dev.1` 增加原子共享预算准入和独立包版本。参见[预算架构](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/ArtCraft-Budget-Architecture.zh_CN.md)。版本 0 的默认在线首次使用及受控 Codex 安装已通过；版本 1 的证据单独记录。

版本 1 在线证据：[首次使用与有界 Logo 返工](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v1.json)、[Codex 安装入口](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/codex-installation-v1.json)。两个修订均交付原生工程，旧工程摘要和音频不变，重跑去重，第三个修订因轮次上限被拒绝。

开发版本 `0.1.0-dev.3` 接通公开原生源工程修订；四领域真实修订和 59 项串行运行时测试通过，并行 EffectCraft 测试偶发失败仍待解决。[架构](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/ArtCraft-Runtime-Architecture.zh_CN.md)。

[版本 3 默认在线首次安装及原生 Logo 修订证据](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v3.json)。使用 dev.3；dev.2 因运行时自报版本不匹配被安装器拒绝，已注明不可使用。

开发版本 `0.1.0-dev.4` 固定四领域技能源 dev.1：修复 CLI 安装/复用的非阻塞锁竞争，改为有界等待。此前并行失败已稳定复现并消除；16 个 EffectCraft 并行样本与 59 项并行原生回归通过。

[版本 4 默认在线首次使用证据](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v4.json)：四个新技能发布包和运行时通过默认公开地址下载、摘要校验与原生项目修订。

开发版本 `0.1.0-dev.5` 增加公开项目打包/移动验包入口，保留原生工程、素材、预览、导出、登记输入和任务记录。实际删除原目录后，四领域原生工程重开与导出通过；技术待审状态不提升为创作验收。

[版本 5 默认在线首次使用及公开打包/移动验包证据](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v5.json)。工作目录保留 SQLite 账本供本地继续工作；便携项目包提供冻结计划和任务记录，不复制活跃账本。

开发版本 `0.1.0-dev.6` 使用独立 worker 监督原生执行。调度器退出后重跑同一冻结工作流，接管已持久化停止证据、验收同一 attempt，预算不重复分配。macOS arm64 调度器 SIGKILL 与真实 EffectCraft 渲染接管通过；worker 自身崩溃或提交窗口未知时保留写占用，不重放副作用。

dev.6 默认在线首次使用从单独复制的技能与空运行时开始、无离线覆盖，52.278 秒通过。验收实际杀死安装后的调度器，并通过同一公开 workflow 入口恢复原 attempt，预算不重复占用；源工程修订、项目打包移动验证同时通过。证据：[在线验收](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v6.json)。

开发版本 dev.7 安装四领域 dev.2 并核验摘要绑定交换报告，检查原生/导出/重开记录身份、派生物边界与未知保真；报告随项目打包。完整跨编辑器保真验收仍待完成。

dev.7 默认在线首次使用从一个复制技能与空运行时开始、无离线覆盖，53.106 秒通过。四个原生交付含摘要绑定交换报告，源工程修订、原任务恢复和移动包核验通过。[证据](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v7.json)。

## CLI 与场景技能体系

[ArtCraft Skill Suite Architecture](docs/ArtCraft-Skill-Suite-Architecture.zh_CN.md)

| 技能 | 用途 |
| :--- | :--- |
| `artcraft-use` | 组合多个本工具能力并保留可编辑原生交付 |
| `artcraft-cli` | 查询实际命令参数和能力，调用公开 CLI、MCP 与诊断 |
| `artcraft-cli-setup` | 首次安装、摘要校验、版本检查与缺失运行时排障 |
| `artcraft-cli-plan` | 拆解品牌图形、海报、片头与宣传片的工具、DAG 和交付约束 |
| `artcraft-cli-execute` | 执行已有 ArtCraft 计划，核对输入版本与并发写入 |
| `artcraft-cli-assets` | 登记素材摘要、来源与子工程依赖，核对受影响产物 |
| `artcraft-cli-revise` | 替换 Logo 或指定资产，修改原生子工程并更新下游 |
| `artcraft-cli-recover` | 检查任务状态、取消原任务并在调度器退出后恢复 |
| `artcraft-cli-deliver` | 收集原生子工程、素材、计划和证据，移动包后核验 |
| `artcraft-cli-review` | 检查混合交付的技术证据和视觉文案音频一致性 |

`npx skills add full-aigc-skills/artcraft-skills --skill <skill-name>`

命令统一使用 `SKILL_DIR`，其值为宿主实际加载的 `SKILL.md` 所在绝对目录。支持用户级、项目级 `.agents/skills` 及插件内部或缓存目录；CLI 运行时另外安装到用户数据目录。每个技能单独复制到三种含空格的布局后，文档中的脚本入口均可运行 `--help`。[路径验证](docs/evidence/installed-skill-paths.json)。既有宿主缓存需更新后才会收到修正文档。

技能源 dev.10 固定 PhotoCraft/VectorCraft dev.5，新增无离线制品覆盖的默认公开下载工作流验收。单独复制 ArtCraft 技能后安装 Node 与四个原生 CLI，交付四份原生工程，复用相同任务、拒绝非法计划修订，并完成交付打包/移动/验包。回归 20 项通过、1 项 Node 专用离线制品测试跳过；在线混合流程实际安装了 Node。[证据](docs/evidence/online-domain-upgrade.json)。运行时保持 dev.7；创作与完整宿主/模型验收仍未完成。

技能套件 dev.11 修正过期工作流与恢复说明，补充单场景技能隔离验收：仅安装 artcraft-cli-revise，在空运行时中默认公开下载全部依赖；登记旧原生工程后修改 Logo 和受影响产物，复用无关节点，保留旧工程摘要、动画、音轨、字幕以及重复调用的任务与预算身份。随后逐次仅保留 assets/deliver/review/recover 技能目录，查询账本、打包、移动验包并幂等取消已停止任务。这不证明 worker 崩溃恢复或创作质量通过。[证据](docs/evidence/task-skill-first-use.json)。运行时和领域制品保持此前已验证的固定版本。

技能套件 dev.12 固定运行时 dev.13，加入可选 Video Factory 0.4.0 公开验证节点。选用的外部插件及 FFmpeg/ffprobe 须已安装并按实际路径登记；ArtCraft 自动安装自身固定依赖。候选隔离首次使用以本地锁定 ArtCraft ZIP、公开 Node/领域 CLI 下载通过，保留来源 NOT_RUN 和真实报告打包。默认公开运行时下载在制品发布后单独验证，不能用候选证据替代。[候选证据](docs/evidence/video-factory-candidate.json)。此适配不提供旧插件渲染、剪映转换或创作验收。

制品发布后的默认在线回归：172.375 秒，24 项通过、1 项 Node 专用离线制品测试跳过；未传入本地运行时、Node 或原生制品覆盖。隔离技能执行五节点，将报告绑定到真实成片摘要，复用任务身份并验证五份子交付打包。[在线证据](docs/evidence/video-factory-online.json)。运行时 dev.13 和技能源标签 dev.12 保持不可变；宿主/模型及创作验收仍未完成。

技能套件 dev.13 固定 EffectCraft 技能 dev.6，编排运行时保持 dev.13。单独安装返工技能后默认公开下载依赖，修改原生蒙版顶点，仅更新片头/成片并复用 Logo/海报；保留原文件摘要、透明度关键帧、音轨和字幕，RGBA 边界及四子交付验包通过。完整默认在线回归 25 项通过、1 项 Node 专用离线测试跳过；当前原生集成 83 项通过。[架构](docs/ArtCraft-Mask-Revision-Architecture.zh_CN.md)、[证据](docs/evidence/mask-revision-first-use.json)。宿主/模型与创作验收仍未完成。

技能套件 dev.14 固定编排运行时 dev.16 和 FilmCraft dev.5（维护版 CLI 0.2.0-craft.1），支持完整 Git 发布 ZIP 与原工程媒体保留绑定。单返工技能默认在线冷启动完成四工程、中文配音及字幕烧录，字幕修订仅更新 FilmCraft，保留旧文件、音轨及三个任务身份；2 项测试通过，成片 72 帧，四子交付验包通过。[架构](docs/ArtCraft-Chinese-Mixed-Architecture.zh_CN.md)、[证据](docs/evidence/chinese-mixed-first-use.json)。完整创作、GUI 与模型调度验收仍待完成。

技能套件 dev.15 保持编排运行时 dev.16，按任务图选择依赖：仅 Logo 时只安装 VectorCraft；新增海报时增量安装 PhotoCraft；未登记执行器在下载前失败。手动 bootstrap 完整安装默认保持兼容，可用 --plugin 或 --runtime-only 缩小安装范围。[按需安装架构](docs/ArtCraft-Selected-Setup-Architecture.zh_CN.md)。当前发布状态和测试范围以对应证据为准。

按需安装最终默认在线回归：36 项中 35 项通过、1 项 Node 离线制品测试未运行（297.920 秒）；运行源码摘要与开始时一致。[证据](docs/evidence/selected-domain-first-use.json)。

技能源 dev.16 补齐十个技能的首次使用指引：先用 --runtime-only 安装编排运行时，workflow.py 再按任务图安装领域；修正可选 Video Factory 验证仍被写成未接入的旧描述。运行脚本与 dev.15 在线回归完全相同；新增指引门禁及既有守卫 6 项通过、1 项已验证原生用例未在此静态运行中重复。

技能源 dev.17 为每个可独立安装的技能增加 `review.py record/verify`：绑定当前验包与资产版本，复制具名观察为可移动的包外审阅记录，分别记录工程、技术、创作和人工接受。账本不提升状态，缺项保持 pending。6 个单元测试和 1 个单技能默认公开下载首次使用测试通过；测试观察仅证明记录合同，不证明创作验收。[架构](docs/ArtCraft-Review-Records-Architecture.zh_CN.md)、[指南](skills/artcraft-use/references/review.md)。编排运行时仍为 dev.16。

技能套件 dev.18 增加独立返工脚本，支持冻结策略、已核验的当前交付包与审阅、明确的原生补丁。它更新受影响子工程、复用无关任务并保留原交付。真实首次使用测试通过轮次、停滞、预算停止与进程中断恢复。[架构](docs/ArtCraft-Revision-Cycle-Architecture.zh_CN.md)。反馈 fixture 不代表创作验收；模型生成补丁和完整宿主验收仍未完成。

当前固定发行版混合审阅：插件 dev.20、技能源 dev.18 的实际安装内容通过两项中文原生首次使用／返工测试。当前助手查看四个真实输出，保存摘要绑定的模型观察并重新核验。仅改字幕的 v2 测试刻意保留原配音、改变文字，因此文案与配音一致性为 FAIL；工程／技术 PASS 不代表创作验收。人工接受仍为 NOT_RUN。[证据](docs/evidence/installed-mixed-observation.json)。本次 QA 未创建新原生发行版或新模型会话。

技能源 dev.19 在停止回执保留未解决失败快照，问题所属包／审阅与最佳包分别绑定。旧日志返回 NOT_RUN，不能把空数组当作无问题。十项单元测试及一项独立技能默认在线原生首次使用测试通过。[证据](docs/evidence/revision-unresolved-first-use.json)。运行时保持 dev.16，完整创作与宿主验收仍独立记录。

单技能在线冷启动品牌色混合工作流验证通过：图形、海报、片头、成片更新，独立图标任务复用，旧交付保留。VectorCraft 技能固定 dev.6，ArtCraft 运行时保持 dev.16。技能源 dev.20 已发布，插件 dev.22 已发布；58 个技能的固定发行版宿主发现通过，安装后单技能在线冷启动混合验证通过（54.471 秒）。实际 npx 独立安装与模型派发仍待验证。[架构](docs/ArtCraft-Brand-Token-Mixed-Architecture.zh_CN.md)、[证据](docs/evidence/brand-token-mixed-first-use.json)。

默认 Homebrew Python 3.14.3 通过 58 个逐一独立复制的公开 CLI 入口验证。五领域缓存初始为空，后续同领域探测复用已核验缓存；技能摘要不变。此证据覆盖启动器安装与查询，不替代真实 npx 安装或创作验收。[架构](docs/ArtCraft-Default-Python-Architecture.zh_CN.md)、[证据](docs/evidence/default-python-cli-first-use.json)。

实际宿主安装后的 ArtCraft 混合工作流也通过 Homebrew Python 3.14.3 复验：安装、原生创作、品牌色选择性返工和打包均使用该 Python（2 项测试，49.322 秒）。图像断言使用单独的测试专用 Pillow 进程。[默认 Python 证据](docs/evidence/default-python-cli-first-use.json)。

依赖候选 dev.21 固定 VectorCraft 技能 dev.7 和运行时自带示例字体。单技能冷启动原生混合创建、修订与打包验证通过（2 项，56.437 秒）；当前候选的固定宿主安装验收仍为 NOT_RUN。[证据](docs/evidence/vector-font-mixed-first-use.json)。

已发布技能 dev.21／插件 dev.23 固定宿主发现 58 个技能通过；实际安装的单技能使用默认 Python 3.14.3 冷启动完成原生混合验收（2 项，54.673 秒），全部安装摘要不变。[证据](docs/evidence/codex-release25-vector-font-mixed-20261006.json)。

候选技能 dev.22 修复普通和中文宣传模板的默认矢量文字字体，明确使用随运行时提供的 Source Sans 3。旧普通模板升级依赖后 Logo 节点失败；修正后两个单技能公开冷启动流程分别通过（各 2 项，52.807／52.964 秒）。新固定发布版安装复验仍为 NOT_RUN。[证据](docs/evidence/default-campaign-font-first-use.json)。

已发布技能 dev.22／插件 dev.24 的全部 58 个技能固定宿主发现通过。实际安装单技能冷启动普通源工程返工（2 项，57.177 秒）和中文交付／字幕修订（2 项，57.973 秒）均通过，全部安装摘要不变。此前候选 NOT_RUN 描述发布前检查点。[证据](docs/evidence/codex-release26-default-campaign-20261006.json)。

技能候选 dev.23 修复冻结修订冲突时先覆盖安装回执的问题：先核对绑定，再发布项目安装身份。独立技能公开冷启动、重复执行、运行时登记冲突及移动交付包验证通过（3 项，92.662 秒）；新固定插件安装复验仍为 NOT_RUN。[架构](docs/ArtCraft-Frozen-Revision-Metadata-Architecture.zh_CN.md)、[证据](docs/evidence/frozen-revision-metadata-first-use.json)。

已发布插件 dev.25／技能 dev.23 的实际安装单技能原生冷启动、重放和冲突元数据保全通过（3 项，90.697 秒）；宿主发现及执行后摘要核验覆盖全部 58 技能。[证据](docs/evidence/codex-release27-binding-metadata-20261006.json)。

运行时 dev.26 修复跨授权范围的旧任务复用。候选技能源 dev.24 固定其不可变制品，保留同范围选择性复用，同时核对原生产任务授权。单技能原生冷启动通过（20.006 秒）；最终固定插件安装复验仍为 NOT_RUN。[架构](docs/ArtCraft-Authorization-Reuse-Architecture.zh_CN.md)、[证据](docs/evidence/authorization-reuse.json)。

已发布插件 dev.27／技能 dev.24／运行时 dev.26 的实际安装原生授权范围测试通过（1 项，23.649 秒），四领域首次使用／重放／冲突保全／移动验包回归通过（3 项，95.854 秒），全部 58 个安装摘要不变。[证据](docs/evidence/codex-release28-authorization-native-20261006.json)。

ArtCraft Brief 源更新锁定运行时 dev.28，支持不可变需求记录、安装前评估和按节点需求指纹。单技能在线冷安装测试通过（3 项，98.048 秒），插件同步及实际安装宿主验证尚待完成。[架构](docs/ArtCraft-Versioned-Brief-Architecture.zh_CN.md)。

已发布插件 dev.29／技能 dev.25／运行时 dev.28 的实际安装 Brief 在线首次使用复验通过（3 项，89.841 秒），五插件 58 个技能发现通过且执行后摘要不变。整体实现仍未完成。[证据](docs/evidence/codex-release29-brief-native-20261006.json)。

源候选 dev.26 锁定 PhotoCraft 技能 dev.6，支持受保护的局部源工程修改。独立在线 Photo-only 创建／拒绝／修订／移动验包通过（1 项，19.902 秒），固定插件验收尚待完成。运行时仍为 dev.28。[架构](docs/ArtCraft-Photo-Protection-Architecture.zh_CN.md)。

固定 PhotoCraft 插件 dev.7／技能 dev.6 与 ArtCraft 插件 dev.30／技能 dev.26 的实际安装原生保护／交接复验通过；五插件全部 58 个技能摘要不变。只完成对应保护任务，整体实现和创作接受仍未完成。[证据](docs/evidence/codex-release30-protected-native-20261006.json)。

源码候选 dev.27 固定 PhotoCraft 技能源 dev.7，支持带保护检查的公开修图工作流；运行时仍为 dev.28。安装后插件复验尚待完成，整体目标未完成。

固定 PhotoCraft 插件 dev.8／技能源 dev.7 与 ArtCraft 插件 dev.31／技能源 dev.27 通过安装后的原生修图和交接测试（13.260 秒／23.264 秒）。58 个安装后技能摘要全部保持不变。仅完成有界修图任务；完整目标仍未完成。[证据](docs/evidence/codex-release31-retouch-native-20261006.json)。

源码候选 dev.28 固定运行时 dev.32，提供有界失败诊断。单技能全新在线 PhotoCraft 集成通过（21.660 秒），覆盖保护失败报告、公开状态查询、重复调用保持 attempt、合法修订和移动包。安装后的插件证据仍待完成。[证据](docs/evidence/native-failure-diagnostics.json)。

固定 ArtCraft 插件 dev.33／技能源 dev.28／运行时 dev.32 通过安装后的失败／状态／重复执行测试（1 项，26.233 秒）及四领域在线首次使用回归（3 项，95.701 秒）。58 个已安装技能摘要全部保持不变。仅完成有界任务 5.12；完整实施和创作接受仍未完成。[证据](docs/evidence/codex-release33-diagnostics-native-20261006.json)。

源码候选 dev.29 锁定运行时 dev.34，首次使用混合示例加入一秒 Film Brief 要求。运行时在发布就绪产物及复用前核对保存后原生时间线和实际成片探测。在线冷安装及安装后插件证据待完成；源工程 Brief 检查和完整创作验收仍未完成。

技能源候选 dev.29 在线冷安装首次使用通过：3 项、93.401 秒。保存后 Film 工程为一秒，成片、原生检查记录和工程摘要绑定已核验。固定插件安装后验收仍待完成。

固定 ArtCraft 插件 dev.35／技能源 dev.29／运行时 dev.34 已通过实际安装技能的在线首次使用（3 项、94.638 秒），包含一秒原生 Film 时长与成片探测摘要绑定检查。58 个安装技能摘要保持不变。源工程 Brief 检查及完整实施／创作验收仍未完成。 [Evidence](docs/evidence/codex-release35-film-duration-native-20261006.json)。

本地 Film 源工程 Brief 候选在写入前使用固定原生 CLI 读取真实元数据，支持字幕与镜头修订，并在就绪发布前拒绝原生导出成功但时长不符的结果。实际本地原生回归通过；固定发行及安装后的源工程首次使用待完成。Photo／Effect／Vector 源工程 Brief 检查及整体验收仍未完成。 [Architecture](docs/ArtCraft-Film-Source-Brief-Architecture.zh_CN.md)。

本地候选更新：Photo／Effect／Vector 源 Brief 已接入保存后原生门禁、主 PNG 尺寸、Effect 实际视频探测与缓存复验。真实源返工、尺寸调整与错误结果拒绝本地通过；固定发布冷启动验收仍开放，尚未发布新版本或更新托管技能快照。

[Photo variant integration / 尺寸变体集成](docs/ArtCraft-Photo-Variant-Integration-Architecture.md) · [中文](docs/ArtCraft-Photo-Variant-Integration-Architecture.zh_CN.md) · [Evidence](docs/evidence/photo-variant-integration.json).

Fixed-release proof / 固定发行验收：[dev.40 Photo variant mixed first use](docs/evidence/codex-release40-photo-variant-first-use-20261006.json). Five fixed plugins / 58 skills, cold mixed workflow, selective Logo rework, moved geometry package and tamper rejection; technical evidence only.

[Variant reuse gate](docs/ArtCraft-Photo-Variant-Gate-Architecture.md) · [中文](docs/ArtCraft-Photo-Variant-Gate-Architecture.zh_CN.md) · [Evidence](docs/evidence/photo-variant-gate-native.json).

[Fixed dev.42 variant reuse gate / 尺寸变体复用固定验收](docs/evidence/codex-release42-variant-gate-first-use-20261006.json).

ArtCraft 技能源 dev.33 固定 FilmCraft 技能 dev.6，保留运行时 dev.41。公开冷启动 3/3 通过，覆盖原生回执异常拒绝、全部项目文件保留、恢复后复用原任务 ID、四种源工程修订和移动包验证。默认回归 66 项通过、13 项可选跳过。[架构](docs/ArtCraft-Film-Receipt-Integration-Architecture.zh_CN.md)、[源码证据](docs/evidence/film-receipt-integration-native.json)。固定插件 dev.43 宿主证据见下方；完整创作验收仍待完成。

[固定安装首次使用证据](docs/evidence/codex-release43-film-receipt-first-use-20261006.json)。保留不可变发行标签；QA 修改仅加强版本绑定与实际导出像素断言。

五套技能逐项空运行时复验 **58/58 通过**（411.720 秒）：每项仅复制自身，使用独立空运行时自动安装、查询原生版本并核对命令合同；随后删除该运行时。全部原安装技能摘要不变。此项加强此前按领域共用运行时的 CLI 验收，仍不替代场景创作或模型验收。[证据](docs/evidence/codex-release43-every-skill-cold-first-use-20261006.json)。

安装后的恢复技能从空运行目录首次使用，真实调度器 SIGKILL 后独立 worker 留下停止证据；公开工作流重开同一原生 attempt，不重放、不增加预算，视频确认 96 帧。[崩溃接管验收](docs/ArtCraft-Scheduler-Crash-Acceptance.zh_CN.md)。worker 崩溃、模型及创作验收仍需独立证据。

dev.44 首次使用已知取消问题：原生运行中取消后，短暂进程组存在性 EPERM 使监督器停止观察，可能保持 `cancel_requested`。运行时 dev.45／技能源 dev.34／插件 dev.46 已发布修复并通过固定公开首次使用取消；dev.44 标签保留原内容。[修复与证据](docs/ArtCraft-Live-Cancel-Architecture.zh_CN.md)。

技能源 dev.34 通过原生运行中取消的空运行目录首次使用（1 项，22.897 秒），使用公开运行时 dev.45。停止后释放的事件顺序、原 attempt、一次启动、预算保留及未发布产物均通过；重复已取消工作流不重放。固定插件 dev.46 安装证据见下方。[源码证据](docs/evidence/live-cancel-source34-first-use.json)。

固定插件 dev.46／技能源 dev.34／运行时 dev.45 已通过公开安装后首次使用：真实原生运行中取消（31.291 秒）、调度器 SIGKILL 接管（29.652 秒）、十项 ArtCraft 技能各自空运行目录冷启动（111.779 秒）及混合回归（3 项通过，114.047 秒）。五插件发现 58 技能、零错误，全部安装摘要保持不变，修复了已记录的 dev.44 取消问题。[版本绑定证据](docs/evidence/codex-release46-live-cancel-first-use-20261006.json)。

安装后的 dev.46 截止时间验收通过：恢复技能从空运行目录安装选定依赖，随后四秒执行期限停止实际原生渲染，确认停止后释放占用，依赖消费者未启动。重跑保留原 attempt／预算且不重放。[期限证据](docs/ArtCraft-Deadline-Acceptance.zh_CN.md)。安装时间不计入该执行期限。

必需源音轨失败传递已通过本地候选真实混合测试：保留诊断、阻断后续任务且不重复执行；正常音轨与增益返工同样通过。后续固定公开发行复验记录如下。[方案与候选证据](docs/ArtCraft-Required-Audio-Architecture.zh_CN.md)。

固定 ArtCraft dev.49 在 Codex 0.153.4 首次使用复验通过：58 技能、零加载错误；安装后的混合缺源音轨失败与正常增益返工，以及十项 Art 技能逐项空运行时启动。全部安装摘要保留。[发行绑定证据](docs/evidence/codex-release49-required-audio-mixed-first-use-20261006.json)。完整首版／模型／GUI／创作验收仍开放。

技能源 dev.37 锁定不可变 Vector dev.9／原生 craft.2，保留 runtime dev.48。五节点公开冷启动品牌返工通过，包含无关 SVG／PNG／PDF 保全、任务选择性复用、重复预算及子工程验包；固定新插件首次使用仍待完成。[架构](docs/ArtCraft-Vector-PDF-Identity-Architecture.zh_CN.md)。

固定 ArtCraft dev.50／VectorCraft dev.10 的 Codex 0.153.4 隔离首次使用通过：五插件 58 技能发现、零加载错误；单导出技能空运行时跨秒原生验收 1 项通过（8.108 秒），混合品牌返工 2 项通过（51.409 秒），全部安装摘要保留。[发行绑定证据](docs/evidence/codex-release50-vector10-stable-export-first-use-20261006.json)。通用 Skills CLI 安装、模型／GUI、完整领域与创作验收仍开放。

本次更新的 22 个技能逐项公开冷启动全部通过（159.811 秒）：每项只复制自身目录到 .agents/skills，独立空运行时完成版本与命令合同检查，目录摘要和全部宿主安装摘要保留。该证据不代表通用 Skills CLI 安装或全部创作场景。

固定 dev.53 首次使用：58 技能发现／零错误、十项 Art 独立冷启动（110.577 秒）、安装后真实失败及修正混合交付（56.202 秒）、五个锁定包可重建且原安装 58 项技能摘要不变。[证据](docs/evidence/codex-release53-effect-mapping-first-use-20261006.json)。通用 Skills CLI、完整创作首版、模型／GUI 与生产门禁仍开放。

[PCM WAV 架构](docs/ArtCraft-PCM-WAV-Architecture.zh_CN.md)。

固定 dev.55 PCM WAV 首次使用通过：58 技能／零错误；五子工程原生交付及迁移验包（53.972 秒）；十项 Art 独立冷启动（111.799 秒）；原安装 58 技能摘要保全。[证据](docs/evidence/codex-release55-pcm-wav-first-use-20261006.json)。不关闭通用 Skills CLI、完整首版、模型／GUI 或创作验收。

固定 dev.57 PNG 首次使用：五插件／58 项技能发现／零加载错误；安装副本的单独 PNG 输入、原样暂存及 Photo 迁移验包通过；PCM 五子工程交付亦通过。十项 Art 独立冷安装用时 132.642 秒，全部 58 项安装技能摘要保全。[版本绑定证据](docs/evidence/codex-release57-png-first-use-20261006.json)。模型／GUI、通用 Skills CLI、完整首版与创作验收仍开放。

技能源 dev.42 固定已发布 Art runtime dev.60 与不可变 Vector 源 dev.10，登记 PNG／JPEG 可进入受管理的 Vector 工作流。单独复制公开 revise 技能测试覆盖 Vector 到 Photo、源素材替换、选择性复用与移动验包；新完整插件安装验收单独进行。[架构](docs/ArtCraft-Vector-Assets-Architecture.zh_CN.md)。

技能源 dev.42 同时固定 Photo 技能源 dev.9，修复纯图片字体前置条件。公开冷启动 Vector／Photo 创建、替换、选择性复用与移动包验收通过；新版完整插件实际安装仍待复验。[证据](docs/evidence/vector-assets-public-candidate-20261006.json)。

技能源 dev.42 默认回归 98 项：75 通过、23 项开关跳过。公开四工具首用 3 项通过，包含真实原生混合创建／修订／恢复／打包（104.465 秒）。固定插件宿主复验单独执行。[证据](docs/evidence/source42-four-domain-candidate-20261006.json)。

固定已安装矩阵 Film9／Effect8／Photo10／Vector11／Art61 通过登记 PNG／JPEG 的 Vector→Photo 替换复用（1 项）、四领域原生首用／恢复／打包（3 项），以及更新的 Photo／Art 全部 22 技能独立空缓存 CLI 检查（190.051 秒）；58 个安装技能摘要保持不变。SVG 混合输入、动态透明序列与完整创作验收仍开放。[证据](docs/evidence/codex-release61-vector-photo-first-use-20261006.json)。

技能源 dev.43 单独复制、默认公开冷安装的 PNG／JPEG 与 SVG 混合首用两项通过（55.457 秒），覆盖外部 SVG 明确拒绝、非目标像素保持、PSD 独立解码、选择性返工、重复任务复用和迁移打包。[源码候选证据](docs/evidence/svg-mixed-source43-candidate-20261006.json)。固定完整插件 dev.63 安装复验通过；完整首版仍开放。

固定 ArtCraft 插件 dev.63／技能源 dev.43／runtime dev.62：隔离 Codex 发现五插件／58 技能／零错误；安装后 PNG／JPEG 与 SVG 混合首用 2 项通过（76.574 秒）、四领域回归 3 项通过（116.076 秒）、Art 十项独立冷启动通过（133.395 秒）。原安装全部 58 项摘要保全，五包固定重建一致，两份公开发行附件及逐文件摘要匹配。SVG 拒绝保留领域代码；替换只重建消费者，非目标像素保持，PNG／PSD 独立核对且迁移包通过。仅关闭有界固定 SVG 交接门禁；SVG 类型元数据、动态透明序列及完整首版／创作／模型／GUI 仍开放。[固定证据](docs/evidence/codex-release63-svg-first-use-20261006.json)。

技能源 dev.44 单技能默认公开冷启动通过四领域五节点动态交付、Logo 替换消费者更新、独立任务复用、完整帧损坏阻断／恢复与移动包核验（1 项，59.343 秒）。[源码版本证据](docs/evidence/dynamic-source44-first-use-20261006.json) · [架构](docs/ArtCraft-Dynamic-Sequence-Architecture.zh_CN.md)。固定 Art dev.65 安装、动态混合首用及全部 58 项 CLI 冷启动已通过。

固定 Art dev.65／技能源 dev.44／runtime dev.64：五插件 58 技能发现零错误；安装后单技能动态四领域交付与 Logo 替换／恢复通过（1 项，62.100 秒），普通原生源工程局部返工回归通过（1 项原生场景＋1 项合同测试，52.541 秒），全部 58 项独立 CLI 冷启动通过（408.253 秒）。安装摘要保持固定，公开附件、固定重建及默认用户数据目录原生安装已核验。[证据](docs/evidence/codex-release65-dynamic-first-use-20261006.json)。完整首版、通用 Skills CLI、模型／GUI／创作／生产验收仍开放。

技能源 dev.45 锁定 Art 运行时 dev.66 与 Effect 技能源 dev.9，接入整份效果／蒙版计划预检；Art 只持久化闭合诊断码与摘要，阻断依赖任务。其余领域包保留原固定版本。候选源码检查与不可变发行安装验收分别记录。

固定 Art 插件 dev.67／技能源 dev.45／runtime dev.66，接入 Effect 技能源 dev.9：Codex 0.153.4 安装五个固定插件，发现全部 58 技能，加载错误为零。安装后单技能 Effect 拒绝／查询／重复执行／纠正修订验收通过（55.362 秒）；动态四领域 Logo 返工、坏帧恢复及移动五子工程打包通过（63.257 秒）。58 项独立 CLI 冷启动全部通过（422.907 秒），全部安装摘要保全；公开运行时／技能源附件、五包固定重建及默认用户目录安装已核验。[版本证据](docs/evidence/codex-release67-preflight-mixed-first-use-20261006.json)。只关闭 OpenSpec 6.40；通用 Skills CLI 安装及完整首版／模型／GUI／创作／生产验收仍开放。

固定 Art 插件 dev.69／技能源 dev.46／runtime dev.68 安装后的公开 LUT／运动返工与失败恢复通过（37.836 秒）；十项 Art 独立冷启动通过（111.456 秒），58 安装技能摘要保全，公开附件和五包重建通过。[证据](docs/evidence/codex-artcraft69-lut-motion-first-use-20261006.json)。完整首版仍开放。

2026-10-06 固定智能对象混合验收：Art 插件 dev.70／技能源 dev.47／运行时 dev.68 与 Photo 插件 dev.11／技能源 dev.10／维护版 CLI 0.2.0-craft.1，通过安装后原生测试一项（64.957 秒）、十项 Art 独立冷启动、58 安装摘要保全、五固定包重建及四项对应提交 CI。Logo 替换保留海报智能对象变换、蒙版及非目标图层；受影响 Logo／海报／片头／影片更新，独立任务复用，成片十二帧独立解码、坏帧恢复及五子工程移动验包通过。[证据](docs/evidence/codex-artcraft70-smart-mixed-first-use-20261006.json)。完整首版、通用 Skills CLI、GUI／模型调度、持久外部链接及外部 PSD 保真仍开放。

技能源 dev.48 固定 runtime dev.71、Film dev.11、Effect dev.10，保留 Photo／Vector dev.10。HD 分段交接已进入固定分发锁，实际安装版验收仍待完成。

固定公开技能源 HD 混合冷启动已通过；安装版仍待完成。[架构与证据](docs/ArtCraft-HD-First-Use-Architecture.zh_CN.md)。

公开工作流回复检查已同步领域技能源候选，并通过有界原生／Art 协议验证。新的固定领域和 Art 分发包仍待发行与实际安装验收。[候选架构](docs/ArtCraft-Public-Workflow-Protocol-Architecture.zh_CN.md) · [证据](docs/evidence/public-workflow-session-candidate-20261007.json)。

领域原暂存保全由 Film18／源16、Effect／Photo／Vector17／源15提供；Art77仍下载旧客户端，Art 集成由 OpenSpec4.9 保持开放。[集成设计](docs/ArtCraft-Failed-Stage-Integration-Architecture.zh_CN.md)。

固定安装场景矩阵通过37个原生场景及6个合同检查，零跳过。Photo测试已从安装后的技能锁读取维护版原生版本，CLI与安装技能未修改。 [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).


固定 Art 插件 dev.79／技能源 dev.53／运行时 dev.78 的有界安装验收通过：五插件58技能零加载错误；24项原生保存后故障均保留并重新打开产品原工程、阻断下游且不重放；四领域恢复模块缺失／摘要错误在写入前拒绝。十项 Art 技能分别从空运行时公开安装 Node＋Art＋四领域（451.537秒）；1080p／24 fps／五秒混合创作、Logo 返工、坏帧恢复及五子工程移动包通过（209.714秒）。58项安装身份保全，五包固定标签重建、两个公开 Art 源ZIP和四项精确插件提交CI通过。仅关闭 OpenSpec4.9；全量2639命令上下文／产物／GUI／修订、通用Skills CLI、模型与完整V1仍开放。[版本绑定证据](docs/evidence/codex-art79-failed-stage-first-use-20261007.json)。

当前固定分发：十项Art＋十二项Vector独立冷启动外观和源返工通过；更新四领域混合任务与五子工程移动包通过。全量命令／GUI／模型／完整V1仍开放。 [Evidence](docs/evidence/codex-art86-vector-appearance-first-use-20261007.json).

当前固定分发：十项Art＋十三项Effect独立冷启动表达式和源返工通过；更新四领域混合任务与五子工程移动包通过。全量命令／GUI／模型／完整V1仍开放。 [Evidence](docs/evidence/codex-art87-effect-expression-first-use-20261007.json).

当前固定分发：十项Art＋十二项Photo独立冷启动蒙版调整和源返工通过；更新四领域混合任务与五子工程移动包通过。全量命令／GUI／模型／完整V1仍开放。 [Evidence](docs/evidence/codex-art88-photo-adjustment-first-use-20261007.json).

[原生路径首次使用架构](docs/ArtCraft-Native-Path-Architecture.zh_CN.md)

固定Art105／源79实际隔离Codex安装64技能零错误、10个安装技能独立冷启动201.746秒及首次模型下载／五子工程真实识别、品牌返工和移动包196.910秒通过。完整V1与通用Skills CLI仍开放。

技能源dev.80固定新不可变Art runtime dev.106，修复公共协议自有字段校验。十个技能携带相同运行时文件摘要，命令证据更新为实际runtime106帮助查询；四领域技能源版本和归档身份保持不变。源码回归与单技能隔离默认公开下载安装通过；固定插件107及安装后创作验收在发布后单独记录。

固定插件 dev.107 安装验收通过：十技能新冷安装、390项协议检查、三项原生混合工作流测试。[Evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/artcraft107-protocol-fixed-first-use-20261008.json).

独立安装依赖边界：当前摘要一致的冷安装记录与 128 项新固定副本安装器／CLI 失败检查验收四领域 SK-002。Art 与通用 Skills CLI 安装继续开放。[设计与证据](docs/Craft-Independent-Setup-Boundary-Architecture.zh_CN.md)。

当前固定协议引用发行矩阵（Film／Effect dev.37、Photo dev.36、Vector dev.34、Art dev.107）已通过隔离 Codex 安装／发现 64 项技能、16 项实际安装所有者文件摘要核对，以及五个全新领域缓存下的 64 项独立公开 CLI 探测。原生场景证据仅对字节一致的技能复用，完整首版仍开放。[固定发行证据](docs/evidence/craft-protocol-authority-fixed-first-use-20261008.json)。

技能源 dev.81 候选固定已发布 runtime dev.108，补充持久工作流任务回执说明；145 项源码测试中 109 项通过、36 项条件跳过，单项源码候选技能默认公开空缓存 CLI 安装通过。当前四领域依赖锁保持既有版本，升级等待 PhotoCraft dev.33 前缀 ZIP 的严格兼容。独立技能源标签和完整插件发行仍未完成。[候选证据](docs/evidence/artcraft108-task-receipt-sdk-candidate-20261008.json)。

源码候选将 Art 领域依赖更新为 Film35／Effect34／Photo33／Vector31，并严格归一化固定 Photo 归档前缀。五个不可变归档精确重建，114 项源码测试通过、36 项条件跳过，且已有真实公开空缓存原生 Photo 返工／打包证据。固定完整插件验收仍待完成。[架构说明](docs/Craft-Domain-Archive-Prefix-Architecture.zh_CN.md)。

固定发行 Film38／Effect38／Photo37／Vector35／Art109 已通过实际隔离 Codex 安装和发现 64 项技能、16 项安装副本协议文件摘要核对、五个全新领域缓存下的 64 项 CLI 探测。十项 ArtCraft 技能分别从空缓存完成原生 Photo 蒙版调整、源工程返工与迁移打包；另外 54 项技能仅复用整个技能摘要一致的历史原生证据。默认维护验收矩阵已更新；通用 Skills CLI 安装、模型调度、GUI 和完整 V1／协议验收仍开放。[本次固定证据](docs/evidence/craft-archive-prefix-fixed-first-use-20261008.json)。

当前 Art109 安装副本的混合品牌返工用例通过：四个受影响产物更新，独立徽标复用，无关画板 SVG／PNG／PDF 和原交付保持不变，五个原生子工程打包核验通过。本次覆盖一项 revise 技能的五节点场景。[固定混合场景证据](docs/evidence/craft-archive-prefix-mixed-brand-first-use-20261008.json)。

小尺寸英文字幕模板按1080行归一修正字号；每项独立技能自含画面尺寸换算、预览及短配音源范围指引。源码原生验证与固定插件首用分别验收。[说明与证据](docs/Caption-Size-First-Use.zh_CN.md)。

Vector33 捆绑升级候选已通过两入口真实混合返工、九变体及移动五子工程包验收。此候选记录早于下方source89/plugin117固定验收。 [Evidence](docs/evidence/art-vector33-gateway-export-candidate-20261008.json).

固定source89/plugin117：十个实际安装技能分别空缓存公开安装Node／核心／Vector33，核对新工作流受信摘要并发现585个原生命令。两入口混合返工均交付九变体，更新消费产物、保留无关图形并验证移动五子工程包。64项安装身份一致，其中54项历史冷启动未重跑。完整V1尚未完成。 [Evidence](docs/evidence/craft-art117-gateway-export-fixed-first-use-20261008.json).

分段指南修订和 Film38 固定依赖已就绪；本次新发行安装验收待独立验证。 [Architecture](docs/ArtCraft-Segmented-Guide-Distribution-Architecture.zh_CN.md).

固定 Film41/source38 与 Art118/source90 首用通过：64项安装身份一致；Film13和Art10分别独立冷安装，41项未变技能仅复用摘要匹配的历史冷安装证据。新Art安装副本通过1080p／24fps／120帧混合创建、Logo依赖返工、坏帧恢复及五子工程迁移；Film通过移动工程文字返工与关键帧保全。完整V1仍开放。 [Evidence](docs/evidence/craft-art118-segment-guide-fixed-first-use-20261008.json).

固定Art119／源91身份与指南分发门禁通过：64项宿主身份及公开CLI核验，十项新独立冷安装，54项仅复用整树摘要一致的历史冷证明；安装的execute技能真实表达式创建、源返工、原工程／非目标像素保全及移动包通过。技能源包清单与套件均为91。只关闭3.28，完整V1仍开放。 [Evidence](docs/evidence/craft-art119-guidance-fixed-first-use-20261008.json).

固定源92／插件120已完成场景安装诊断的有界验收，见下方记录。 [Evidence](docs/evidence/scenario-setup-diagnostics-20261008.json).

固定Art120／源92：十项新独立公开冷安装、64安装身份与CLI核验、20个安装副本真实失败调用、安装失败后公开冷安装／原生图形创建／同任务复用／移动交付恢复通过。54项其他技能仅复用整树摘要相等的历史冷证明。只关闭3.29，完整V1与目标保持未完成。 [Evidence](docs/evidence/craft-art120-scenario-setup-fixed-first-use-20261008.json).

嵌套安装诊断与固定领域检查参数兼容已通过源码回归和真实公开冷恢复；固定发行验收仍开放。 [Evidence](docs/evidence/nested-setup-diagnostics-candidate-20261008.json).

固定Art121／源93通过10项独立公开冷启动、64宿主身份／CLI核验、30条安装副本嵌套拒绝、12项固定领域检查及原生恢复／审阅／返工。54项其他技能仅复用整树摘要相等历史冷证明；只关闭3.30。并行运行时取消时序与完整V1仍开放。 [Evidence](docs/evidence/craft-art121-nested-setup-fixed-first-use-20261008.json).

取消信号ESRCH退出竞态已通过可控真实进程红灯／绿灯与并行／串行回归；固定安装原生验收待完成。 [Architecture](docs/ArtCraft-Cancel-Signal-Architecture.zh_CN.md).

固定Art122／源94／运行时122-runtime.1通过10项独立公开冷启动、64宿主身份／CLI核验，以及安装副本可控ESRCH和普通期限两条原生取消。原attempt／预算保留，下游不启动，重复不重放。54项其他技能仅复用整树摘要相等历史冷证明。只关闭5.19；完整5.9／V1及原偶发并行失败归因仍开放。 [Evidence](docs/evidence/craft-art122-cancel-signal-fixed-first-use-20261008.json).

公共任务协议实施审计已完成 OpenSpec 任务 1.1、1.2：固定107基线复现两项行为失败，当前固定122协议测试135项通过，完整回归255通过／20条件跳过，两次独立公开原生首用通过。1.3仍开放，需补全四领域消费者对新增预算错误码的兼容性及完整公开响应／错误矩阵证据。[审计架构](docs/ArtCraft-Public-Task-Architecture.zh_CN.md) · [证据](docs/evidence/public-task-implementation-audit-20261008.json)。

质量证据分离与受限明确补丁修订已完成任务8.1–8.6：当前固定技能的审阅迁移／篡改拒绝、真实 Film 解码与损坏副本拒绝、三种原生停止策略及中断恢复通过。创作观察为测试声明，不代表真实审美或人工接受；完整 V1 仍未完成。[机制架构](docs/ArtCraft-Quality-Gates-Architecture.zh_CN.md) · [证据](docs/evidence/quality-mechanisms-acceptance-20261008.json)。
