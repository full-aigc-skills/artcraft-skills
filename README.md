# ArtCraft independent skills

The public `artcraft-use` entry is verified from a clean copied directory without global Node or sibling repositories. It installs pinned Node, the ArtCraft runtime, four independent skill snapshots and four official CLIs, then creates Logo, poster, animated intro and video with subtitles/audio while retaining all four native project formats.

This is a development build. Tests use local locked release bundles and actually install the four CLIs from their official sources. Online distribution of the project's bundles and plugin-host installation remain unverified.

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

All 12 skill/installer tests pass, including complete isolated first use and four native project deliveries. The runtime's full 48-test regression also passes. `review_ready` denotes technical readiness. Native source-project revision bindings, shared budgets, final creative review, crash adoption, final packaging and host release remain unfinished.

Specification authority: [ArtCraft OpenSpec](https://github.com/full-aigc-plugins/artcraft-plugin/tree/main/openspec/changes/establish-v1-plugin).

[中文](README.zh-CN.md)
