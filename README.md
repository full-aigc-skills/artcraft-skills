# ArtCraft independent skills

The public `artcraft-use` entry is verified from a clean copied directory without global Node or sibling repositories. It installs pinned Node, the ArtCraft runtime, four independent skill snapshots and four pinned native CLIs, then creates Logo, poster, animated intro and video with subtitles/audio while retaining all four native project formats.

This is a development build. Version 0 passed default online downloads and controlled Codex installation/discovery; version 1 also passes default online first use and installed-skill execution with shared budget admission. Release-specific online evidence is maintained in the plugin repository.

## First use

Requires macOS arm64 and Python 3.11+. Run `scripts/workflow.py` from the actual loaded skill directory; see the [skill entry](skills/artcraft-use/SKILL.md) and [workflow contract](skills/artcraft-use/references/workflow.md). It installs on first use and verifies reuse afterward without changing PATH.

```bash
python3 /absolute/skill/artcraft-use/scripts/workflow.py \
  /absolute/skill/artcraft-use/examples/brand-campaign.json \
  --output /absolute/path/project --authorization project-authorized \
  --asset voice=/absolute/path/voice.wav
```

Provide an existing WAV for this example. Development offline tests add `--node-archive` and `--bundle-dir`; optional `--native-archive-dir` supplies official CLI ZIPs. Offline archives still require exact digest checks.

## Sources and deliveries

| Content | Source of truth | Installation |
| --- | --- | --- |
| Skill, setup and project entry | This independent package | Single skill directory can be copied alone |
| ArtCraft runtime | artcraft-plugin src, schemas, package.json | Locked ZIP and file hashes; atomic installation |
| Four domain skills | Independent `*-skills` packages | Locked generated snapshots; public scripts only |
| Node and four CLIs | Pinned official artifacts | Binary, version, license and actual command checks |

Projects retain installation receipts, frozen plans, SQLite ledger, result receipts and child deliveries. Calls for the same project serialize. Repeated revisions reuse tasks; changed content under the same revision conflicts. New revisions rebuild affected nodes.

## Verification and remaining work

All 14 skill/installer tests pass, including complete isolated first use and four native project deliveries. The runtime's parallel 66-test regression also passes. `review_ready` denotes technical readiness. Provider invoice settlement, final creative review, crash adoption, final creative delivery approval and host release remain unfinished.

Specification authority: [ArtCraft OpenSpec](https://github.com/full-aigc-plugins/artcraft-plugin/tree/main/openspec/changes/establish-v1-plugin).

[中文](README.zh-CN.md)

Development version `0.1.0-dev.1` adds atomic shared budget admission and independent bundle versions. See [budget architecture](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/ArtCraft-Budget-Architecture.md). Version 0 default online first use and controlled Codex installation passed; version 1 evidence is recorded separately.

Version 1 online evidence: [first use and bounded Logo rework](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v1.json), [Codex installed entry](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/codex-installation-v1.json). Both generated two revisions, preserved old project hashes/audio, deduplicated replay and rejected a third revision at the configured cap.

Development version `0.1.0-dev.3` adds public native source revision bindings. Four actual domain source revisions and 59 serialized runtime tests pass; parallel EffectCraft native tests remain intermittent. [Architecture](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/ArtCraft-Runtime-Architecture.md).

[Version 3 default online first use and native Logo revision evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v3.json). At that stage dev.3 superseded dev.2; dev.2 is marked unusable because its installer rejected a runtime self-version mismatch.

Development version `0.1.0-dev.4` pins all four domain skills at dev.1, fixing CLI install/reuse lock contention with bounded waiting. The prior parallel failure was reproduced and eliminated: 16 concurrent EffectCraft samples and 59 parallel native regression tests pass.

[Version 4 default online first-use evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v4.json): the four new skill bundles and runtime pass public downloads, digest verification and native project revision.

Development version `0.1.0-dev.5` adds public package/verify entrypoints retaining native projects, media, previews, exports, registered inputs and task records. All four native projects reopen/export after relocation and deletion of originals; technical readiness is not creative approval.

[Version 5 default online first use and public package/move/verify evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v5.json). The working project retains SQLite for local continuation; the portable package contains frozen plans/task records rather than an active ledger.

Development version `0.1.0-dev.6` moves native supervision into a detached worker. Re-running the same frozen workflow adopts persisted stop evidence, verifies the same attempt and keeps budget allocation unchanged. Scheduler SIGKILL and real EffectCraft render recovery pass on macOS arm64; worker death or an unknown submission window retains ownership and never replays side effects.

Default online dev.6 first use passes in 52.278 seconds from a single copied skill and empty runtime, without archive overrides. It also kills the installed scheduler during native execution and recovers through the same public workflow entry with the original attempt and unchanged budget; source revision and moved project-package verification pass. Evidence: [online acceptance](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v6.json).

Development dev.7 installs domain dev.2 and verifies hash-bound exchange reports. Native/output/inspection identity, derivative-only delivery and unknown fidelity are checked; reports survive project packaging. Full cross-editor fidelity acceptance remains open.

Default online dev.7 first-use acceptance passes in 53.106 seconds with one copied skill and an empty runtime, no archive overrides. Four native deliveries include hash-bound exchange reports; source revision, original-attempt recovery and moved-package verification pass. [Evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v7.json).

## CLI and task skill suite

[ArtCraft Skill Suite Architecture](docs/ArtCraft-Skill-Suite-Architecture.md)

| Skill | Purpose |
| :--- | :--- |
| `artcraft-use` | use |
| `artcraft-cli` | cli |
| `artcraft-cli-setup` | cli setup |
| `artcraft-cli-plan` | cli plan |
| `artcraft-cli-execute` | cli execute |
| `artcraft-cli-assets` | cli assets |
| `artcraft-cli-revise` | cli revise |
| `artcraft-cli-recover` | cli recover |
| `artcraft-cli-deliver` | cli deliver |
| `artcraft-cli-review` | cli review |

`npx skills add full-aigc-skills/artcraft-skills --skill <skill-name>`

Commands use `SKILL_DIR`, the absolute directory of the `SKILL.md` actually loaded by the host. User/project `.agents/skills` and plugin-internal/cache layouts are supported; the CLI runtime is installed separately in the user data directory. Each skill was copied alone into all three layouts, including paths with spaces, and its documented script entry points ran `--help`. [Path verification](docs/evidence/installed-skill-paths.json). Existing host caches need an explicit update to receive the corrected documentation.

Skill suite dev.10 pins PhotoCraft/VectorCraft dev.5 and verifies the default public-download workflow without offline archive overrides. One isolated ArtCraft skill installed Node and four native CLIs, delivered four native projects, reused the same tasks, rejected an invalid plan revision, and packaged/moved/verified the delivery. Regression: 20 passed, one Node-only offline-archive test skipped; the online mixed workflow installed real Node. [Evidence](docs/evidence/online-domain-upgrade.json). Runtime remains dev.7; creative and full host/model acceptance remain pending.

Skill suite dev.11 corrects outdated workflow/recovery instructions and adds isolated task-skill acceptance. The test installs `artcraft-cli-revise` alone with an empty runtime and default public downloads, revises registered native projects, updates Logo consumers while reusing an unrelated node, and checks original project hashes, animation, audio, captions and repeat budget/task identity. It then replaces the installed skill directory with assets/deliver/review/recover one at a time to inspect the ledger, package/move/verify and idempotently cancel a stopped task. This does not establish crashed-worker recovery or creative approval. [Evidence](docs/evidence/task-skill-first-use.json). Runtime and domain bundles remain pinned at their previously verified versions.

Skill suite dev.12 pins runtime dev.13 and adds optional public Video Factory 0.4.0 validation nodes. The selected plugin and FFmpeg/ffprobe must already be installed and explicitly registered by actual paths; ArtCraft still bootstraps its own pinned dependencies. The candidate isolated first-use test passes with a local locked ArtCraft ZIP and public Node/domain CLI downloads, preserving NOT_RUN provenance and packaging the real report. Default public runtime download is verified after artifact publication, separately from this candidate proof. [Candidate evidence](docs/evidence/video-factory-candidate.json). This does not provide legacy rendering, Jianying conversion or creative acceptance.

Post-publication default online regression: 24 passed, one Node-only offline archive test skipped in 172.375 seconds. No local runtime, Node or native archive override was supplied. The isolated skill executes all five nodes, binds the report to the actual film output, reuses task IDs and verifies five packaged child deliveries. [Online evidence](docs/evidence/video-factory-online.json). Runtime dev.13 and source tag dev.12 remain immutable; host/model and creative acceptance are still open.

Skill suite dev.13 pins EffectCraft skills dev.6 while retaining orchestration runtime dev.13. A single installed revise skill cold-installs default public dependencies, edits native mask vertices, updates only intro/video consumers and reuses Logo/poster tasks. Original file hashes, opacity keys, audio and captions remain unchanged; RGBA boundaries and four-child package verification pass. Full default-online regression: 25 passed, one Node-only offline test skipped; current native integration: 83 passed. [Architecture](docs/ArtCraft-Mask-Revision-Architecture.md), [evidence](docs/evidence/mask-revision-first-use.json). Host/model and creative acceptance remain pending.

Skill suite dev.14 pins orchestration runtime dev.16 and FilmCraft dev.5 (maintained native CLI 0.2.0-craft.1). It supports complete Git release ZIPs and explicitly retained source media. One isolated revise skill cold-installs default public dependencies, creates four native projects with Chinese voice and burned captions, then updates only FilmCraft while preserving original files, audio and three task identities. Two tests passed; 72 video frames and all four packaged children were verified. [Architecture](docs/ArtCraft-Chinese-Mixed-Architecture.md), [evidence](docs/evidence/chinese-mixed-first-use.json). Full creative, GUI and model-dispatch acceptance remain pending.

Skill suite dev.15 retains orchestration runtime dev.16 and selects dependencies from the task graph. A Logo-only workflow installs VectorCraft; adding a poster installs PhotoCraft incrementally. Unknown executors fail before downloads. Explicit bootstrap keeps its full-install default for compatibility and supports --plugin or --runtime-only selection. [Selected setup architecture](docs/ArtCraft-Selected-Setup-Architecture.md). Evidence records publication and acceptance scope.

Final selected-setup default-online regression: 35 of 36 tests passed; one Node-only offline fixture was skipped (297.920 seconds). Source fingerprints match the start of the run. [Evidence](docs/evidence/selected-domain-first-use.json).

Source dev.16 aligns all ten first-use skill instructions: bootstrap --runtime-only first, then workflow.py installs task-selected domains. It corrects stale claims that optional Video Factory verification is unavailable. Runtime scripts are identical to dev.15 online-tested scripts; six instruction/guard tests pass, with the already verified live case skipped in this static run.

Skill suite dev.17 adds `review.py record/verify` to every independently installable skill. It binds named observations to verified current package/asset identities, copies evidence into a movable sidecar and separates engineering, technical, creative and human acceptance states. It leaves ledger state unchanged and records missing coverage as pending. Six unit tests and one isolated default-public-download native first-use test pass; fixture observations establish the recording contract, not creative acceptance. [Architecture](docs/ArtCraft-Review-Records-Architecture.md), [guide](skills/artcraft-use/references/review.md). Runtime remains dev.16.

Skill suite dev.18 adds an independent revision helper that accepts a frozen policy, verified current package/review and explicit native patches. It updates affected children, reuses unrelated tasks and preserves originals. Round, stagnation and inherited-budget stops plus interrupted-process recovery passed native first-use tests. [Architecture](docs/ArtCraft-Revision-Cycle-Architecture.md). Fixture feedback is not creative acceptance; model patch generation and full host acceptance remain open.

Current fixed-release mixed observation: installed plugin dev.20 and skills dev.18 passed two Chinese native first-use/revision tests. Four actual exports were inspected by the current assistant and a hash-bound model observation was recorded and reverified. Caption-only v2 deliberately retains the original narration but changes its text, so wording consistency is FAIL; engineering/technical PASS does not imply creative acceptance. Human acceptance remains NOT_RUN. [Evidence](docs/evidence/installed-mixed-observation.json). No new native release or model session was used for this QA check.

Skill source dev.19 adds unresolved failure snapshots to stop receipts. Issue package/review identity is distinct from best-package identity; legacy journals report NOT_RUN rather than an empty-list success. Ten unit tests and one isolated default-public native first-use test pass. [Evidence](docs/evidence/revision-unresolved-first-use.json). Runtime stays dev.16; full creative and host acceptance remain separate.

Native global brand-token mixed workflow passes a single-skill public cold install: logo, poster, intro and film update while the unrelated badge task and original deliveries are preserved. VectorCraft skills are pinned to dev.6; ArtCraft runtime remains dev.16. Skill source dev.20 is published; plugin dev.22 is published. Fixed-release host discovery passes for 58 skills, and the installed single-skill cold native mixed test passes in 54.471 seconds. Actual npx independent installation and model dispatch remain unverified. [Architecture](docs/ArtCraft-Brand-Token-Mixed-Architecture.md), [evidence](docs/evidence/brand-token-mixed-first-use.json).

Existing default Homebrew Python 3.14.3 passes all 58 separately copied public CLI entries. Five domain caches start empty; later same-domain probes reuse verified caches. Skill hashes remain unchanged. This verifies launcher installation and queries, not actual npx installation or creative acceptance. [Architecture](docs/ArtCraft-Default-Python-Architecture.md), [evidence](docs/evidence/default-python-cli-first-use.json).

The actual host-installed ArtCraft mixed workflow also passes with Homebrew Python 3.14.3 invoking installation, native creation, selective brand revision and package verification (2 tests, 49.322 seconds). Image assertions use a separate test-only Pillow process. [Default-Python evidence](docs/evidence/default-python-cli-first-use.json).

Vector dependency candidate dev.21 pins VectorCraft skills dev.7 and bundled sample fonts. Single-skill cold native mixed creation/revision/package tests pass (2 tests, 56.437 seconds); fixed-host installed acceptance of this candidate remains NOT_RUN. [Evidence](docs/evidence/vector-font-mixed-first-use.json).
