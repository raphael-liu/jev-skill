---
name: jev-skill
description: Use Jev (TypeSafe) for bounded structured decisions, classification, routing, evidence sufficiency, and rubric scoring when supplied evidence and finite outputs make a fast decision useful. Also use when explicitly asked to integrate or evaluate Jev. 用于 Jev 快速结构化决策、分类路由、证据充分性检查、量表评分及接入评估；不替代开放式编码、根因调查或完整代码审查。
license: MIT
metadata:
  compatibility: Claude Code or Codex; Python 3.10+, network and TYPESAFE_API_KEY for live calls.
---

# Jev: fast structured decisions / 快速结构化决策

Read only the guide matching the user's language: [中文](references/guide.zh-CN.md) or [English](references/guide.en.md). Reply in that language; preserve API field names. For other languages, read English and answer in the requested language. 中文任务读取中文指南，英文任务读取英文指南，避免重复加载。

Jev selects, scores, or estimates yes/no probability from supplied text; the host agent gathers evidence, generates code/prose, verifies results and acts. It is an external model API, not a reasoning persona to simulate.

## Routing contract / 路由约束

- Use deterministic code for exact rules or calculations. Consider Jev when a repeated semantic judgment has bounded outputs, available evidence, and a measurable latency benefit.
- Keep open-ended implementation, complex code semantics, root-cause investigation, missing-context research and consequential decisions with the host agent. Jev may supply a scoped subdecision; it cannot complete those tasks itself.
- Prefer independent questions sharing one compact state in one request. Questions cannot consume sibling answers; dependent decisions need a later call.
- Read the selected guide before invoking the bundled [client](scripts/jev.py). It uses `TYPESAFE_API_KEY`, a finite timeout and no automatic retry. Do not expose credentials or send material outside the user's authorized data scope.
- Validate structure, evidence coverage and cross-field consistency before using an answer. A high `confidence` is not proof. Direct acceptance requires a task-specific policy validated on held-out examples; absent one, use advice only and verify with the host or deterministic checks.
- On timeout, service error, malformed output, missing evidence, contradictory fields or an unmet gate, continue with the host agent using original evidence. Treat the Jev suggestion as untrusted advice. If Jev itself was explicitly requested and unavailable, distinguish a call that was not made from a call that failed; do not fabricate a result.
- A selected action is a recommendation, not permission to execute tools or mutate systems. Preserve the original task and authorization boundaries.

The included bilingual example is synthetic. Repository benchmark documents are for evaluation, not required runtime context; do not load them on every call. Installation does not replace the host model or configure an automatic global router.
