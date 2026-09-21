# jev-skill

[English](README.md) · [简体中文](README.zh-CN.md)

An open-source Agent Skill that helps **Claude Code and Codex decide when to use Jev**, call its typed decision API, and keep uncertain or unsuitable work with the host agent.

Jev is TypeSafe's fast structured decision model. It returns a choice, score, or yes/no probability from supplied text. This repository provides instructions and a small API client; it does not contain model weights, replace your coding agent, or install a global routing service. It is an independent community project, not an official TypeSafe product.

## Install

The repository is initialized locally. A GitHub remote will be supplied later. **Replace `<owner/repo>` with the published repository**; it is not an existing installation target yet.

```bash
npx skills add <owner/repo>
# Explicit selection for both supported coding agents:
npx skills add <owner/repo> --skill jev-skill --agent claude-code codex
```

For a local checkout, run from the project where you want the skill installed:

```bash
npx skills add /absolute/path/to/jev-skill --skill jev-skill --agent claude-code codex
```

Add `--global` for a user-wide installation, or `--list` to inspect available skills without installing. This uses the standard [skills CLI](https://skills.sh/docs/cli) and [Agent Skills format](https://agentskills.io/specification). No npm package publication or custom plugin is required. The installable directory is `skills/jev-skill/`; it contains all runtime references, examples and the client. Repository `docs/` is not needed at runtime.

## Use

Ask the agent naturally, for example:

> Use jev-skill to classify these anonymized diagnostic reports under the attached protocol. Keep unknown cases with you and report actual calls and usage.

> 使用 jev-skill 判断这些已脱敏材料是否足够支持下一步诊断；证据不足时由你继续核验。

The skill follows the user's language and loads only its matching guide. English and Chinese guides and synthetic request examples are included. This is documentation support for both languages, not a claim of equal model accuracy.

For a live call, supply a TypeSafe API key as `TYPESAFE_API_KEY` through your shell or secret manager. Do not commit it or paste it into an agent conversation. Python 3.10+ is required; no third-party Python packages are needed. From the repository root:

```bash
# Local validation only; no key, network request or charge:
python3 skills/jev-skill/scripts/jev.py --request skills/jev-skill/assets/triage.en.json --dry-run
# One real API request using the already configured environment variable:
python3 skills/jev-skill/scripts/jev.py --request skills/jev-skill/assets/triage.en.json --timeout 10
```

The client supports Choice, Score and Noul in one request. It validates the response and emits JSON; an error exits with code 2. It makes no automatic retries, starts no nested agent session and never executes a selected action. Its socket timeout is configurable; the host should enforce an overall deadline if one is required. Read the [English guide](skills/jev-skill/references/guide.en.md) or [Chinese guide](skills/jev-skill/references/guide.zh-CN.md) for API semantics, acceptance gates and fallback handling.

## When it helps

| Prefer a scoped Jev decision | Keep with the host or deterministic code |
|---|---|
| Repeated finite-label routing with evidence already available | Open-ended coding, research and root-cause investigation |
| Evidence sufficiency or choosing among known candidates | Retrieving missing evidence or generating novel answers |
| Independent rubric scores on a shared compact input | Exact computations and executable checks |
| Diagnostic next-step selection under an explicit protocol | Safety clearance and irreversible execution |

Jev can prioritize review, but a low score must not exclude code from review. A high confidence does not prove correctness. Direct acceptance needs task-specific held-out validation; otherwise treat the result as advice. Installing this skill alone does not guarantee latency or token savings.

## Evidence

Our 2026-09-21 controlled decision test recorded Codex/Jev/cascade exact correctness of **78/80, 66/80, 76/80**, with mean reply latency of **9.86 s, 0.99 s, 3.27 s**. These are bounded two-field decisions using Codex CLI `gpt-5.6-sol` and Jev `jev-1.13.0`, not full application delivery. The separate end-to-end pilot did not establish universal speedups. No Claude Code benchmark was performed.

See [benchmark methods, latency and token tables](docs/benchmarks.md) / [中文实验文档](docs/benchmarks.zh-CN.md), with sanitized numeric data. Provider token counts and cached inputs are reported separately; fewer host calls do not imply the same percentage reduction in total tokens or billed cost.

## Validate and contribute

```bash
python3 -m unittest discover -s tests -v
DISABLE_TELEMETRY=1 npx skills add . --list
```

Tests mock the API and require no secret or paid requests. CI runs tests and both example dry-runs. Changes should preserve English/Chinese parity, self-contained installation, explicit unknown/fallback handling and accurate measurement boundaries. Include tests for client behavior changes; do not submit credentials, internal source material or raw private model responses.

To publish later, replace `<owner/repo>` in both READMEs with the actual name, create an empty public repository, then set its remote and push `main`:

```bash
git remote add origin https://github.com/<owner/repo>.git
git push -u origin main
```

License: [MIT](LICENSE), including the packaged skill. Jev access is provided separately by TypeSafe under its own terms. Official references: [API](https://docs.typesafe.ai/api), [confidence](https://docs.typesafe.ai/confidence), [models](https://docs.typesafe.ai/models).
