# ArtCraft independent skills

The public `artcraft-use` entry is verified from a clean copied directory without global Node or sibling repositories. It installs pinned Node, the ArtCraft runtime, four independent skill snapshots and four official CLIs, then creates Logo, poster, animated intro and video with subtitles/audio while retaining all four native project formats.

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

[Version 3 default online first use and native Logo revision evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v3.json). Use dev.3; dev.2 is marked unusable because its installer rejected a runtime self-version mismatch.

Development version `0.1.0-dev.4` pins all four domain skills at dev.1, fixing CLI install/reuse lock contention with bounded waiting. The prior parallel failure was reproduced and eliminated: 16 concurrent EffectCraft samples and 59 parallel native regression tests pass.

[Version 4 default online first-use evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v4.json): the four new skill bundles and runtime pass public downloads, digest verification and native project revision.

Development version `0.1.0-dev.5` adds public package/verify entrypoints retaining native projects, media, previews, exports, registered inputs and task records. All four native projects reopen/export after relocation and deletion of originals; technical readiness is not creative approval.

[Version 5 default online first use and public package/move/verify evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v5.json). The working project retains SQLite for local continuation; the portable package contains frozen plans/task records rather than an active ledger.

Development version `0.1.0-dev.6` moves native supervision into a detached worker. Re-running the same frozen workflow adopts persisted stop evidence, verifies the same attempt and keeps budget allocation unchanged. Scheduler SIGKILL and real EffectCraft render recovery pass on macOS arm64; worker death or an unknown submission window retains ownership and never replays side effects.

Default online dev.6 first use passes in 52.278 seconds from a single copied skill and empty runtime, without archive overrides. It also kills the installed scheduler during native execution and recovers through the same public workflow entry with the original attempt and unchanged budget; source revision and moved project-package verification pass. Evidence: [online acceptance](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v6.json).

Development dev.7 installs domain dev.2 and verifies hash-bound exchange reports. Native/output/inspection identity, derivative-only delivery and unknown fidelity are checked; reports survive project packaging. Full cross-editor fidelity acceptance remains open.

Default online dev.7 first-use acceptance passes in 53.106 seconds with one copied skill and an empty runtime, no archive overrides. Four native deliveries include hash-bound exchange reports; source revision, original-attempt recovery and moved-package verification pass. [Evidence](https://github.com/full-aigc-plugins/artcraft-plugin/blob/main/docs/evidence/online-first-use-v7.json).
