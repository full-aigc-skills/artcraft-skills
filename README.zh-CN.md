# ArtCraft 独立技能

当前技能源 v0.1.0-dev.31 保留运行时 v0.1.0-dev.36，锁定 PhotoCraft skills v0.1.0-dev.8。默认测试 66 项通过、13 项可选跳过；在线冷安装混合回归 3 项通过，包含四源返工、尺寸记录打包迁移与篡改拒绝。固定宿主复验通过；完整创作验收尚未完成。

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
