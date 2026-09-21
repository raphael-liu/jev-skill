# jev-skill

[English](README.md) · [简体中文](README.zh-CN.md)

An open-source Agent Skill that helps **Claude Code and Codex decide when to use Jev**, call its typed decision API, and keep uncertain or unsuitable work with the host agent.

Jev is TypeSafe's fast structured decision model. It returns a choice, score, or yes/no probability from supplied text. This repository provides instructions and a small API client; it does not contain model weights, replace your coding agent, or install a global routing service. It is an independent community project, not an official TypeSafe product.

## Install

Repository: [raphael-liu/jev-skill](https://github.com/raphael-liu/jev-skill). Install from GitHub after the repository contents have been pushed:

```bash
npx skills add raphael-liu/jev-skill
# Explicit selection for both supported coding agents:
npx skills add raphael-liu/jev-skill --skill jev-skill --agent claude-code codex
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

[SKILL.md](skills/jev-skill/SKILL.md) is a complete English operating specification. It includes setup, API contracts, execution, validation, fallback, and experimental limits without requiring reference guides. Agent replies follow the user's language; Chinese and English README files, supporting guides, and request examples are provided. Language support does not imply equal model accuracy.

For a live call, follow [API key setup](skills/jev-skill/SKILL.md) to create a TypeSafe key, enter it without echoing it, and verify `TYPESAFE_API_KEY` inside the agent’s tool environment. The guide covers CLI/desktop inheritance, `.env` behavior and authentication errors. Do not commit it or paste it into an agent conversation. Python 3.10+ is required; no third-party Python packages are needed. From the repository root:

```bash
# Local validation only; no key, network request or charge:
python3 skills/jev-skill/scripts/jev.py --request skills/jev-skill/assets/triage.en.json --dry-run
# One real API request using the already configured environment variable:
python3 skills/jev-skill/scripts/jev.py --request skills/jev-skill/assets/triage.en.json --timeout 10
```

The client supports Choice, Score and Noul in one request. It validates the response and emits JSON; an error exits with code 2. It makes no automatic retries, starts no nested agent session and never executes a selected action. Its socket timeout is configurable; the host should enforce an overall deadline if one is required. Read the complete [SKILL.md](skills/jev-skill/SKILL.md) for API semantics, acceptance gates and fallback handling.

## When it helps

| Prefer a scoped Jev decision | Keep with the host or deterministic code |
|---|---|
| Repeated finite-label routing with evidence already available | Open-ended coding, research and root-cause investigation |
| Evidence sufficiency or choosing among known candidates | Retrieving missing evidence or generating novel answers |
| Independent rubric scores on a shared compact input | Exact computations and executable checks |
| Diagnostic next-step selection under an explicit protocol | Safety clearance and irreversible execution |

Jev can prioritize review, but a low score must not exclude code from review. A high confidence does not prove correctness. Direct acceptance needs task-specific held-out validation; otherwise treat the result as advice. Installing this skill alone does not guarantee latency or token savings.

## Evidence

Our 2026-09 controlled decision test recorded Codex/Jev/cascade exact correctness of **78/80, 66/80, 76/80**, with mean reply latency of **9.86 s, 0.99 s, 3.27 s**. These are bounded two-field decisions using Codex CLI `gpt-5.6-sol` and Jev `jev-1.13.0`, not full application delivery. The separate end-to-end pilot did not establish universal speedups. No Claude Code benchmark was performed.

See [benchmark methods, latency and token tables](docs/benchmarks.md) / [中文实验文档](docs/benchmarks.zh-CN.md), with sanitized numeric data. Provider token counts and cached inputs are reported separately; fewer host calls do not imply the same percentage reduction in total tokens or billed cost.

## Validate and contribute

```bash
python3 -m unittest discover -s tests -v
DISABLE_TELEMETRY=1 npx skills add . --list
```

Tests mock the API and require no secret or paid requests. CI runs tests and both example dry-runs. Changes should preserve English/Chinese parity, self-contained installation, explicit unknown/fallback handling and accurate measurement boundaries. Include tests for client behavior changes; do not submit credentials, internal source material or raw private model responses.

License: [MIT](LICENSE), including the packaged skill. Jev access is provided separately by TypeSafe under its own terms. Official references: [API](https://docs.typesafe.ai/api), [confidence](https://docs.typesafe.ai/confidence), [models](https://docs.typesafe.ai/models).
