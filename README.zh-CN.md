# jev-skill

[English](README.md) · [简体中文](README.zh-CN.md)

帮助 **Claude Code 和 Codex 判断何时适合使用 Jev**、调用结构化决策 API，并将不确定或不适合的任务交回宿主 Agent 的开源技能。

Jev 是 TypeSafe 的快速结构化决策模型，根据给定文本返回选项、评分或是/否概率。本仓库提供技能指令和轻量客户端，不包含模型权重，不替换编码 Agent，也不安装全局路由服务。这是独立社区项目，并非 TypeSafe 官方产品。

## 安装

GitHub 仓库：[raphael-liu/jev-skill](https://github.com/raphael-liu/jev-skill)。仓库内容推送后，可使用以下命令安装：

```bash
npx skills add raphael-liu/jev-skill
# 明确安装到两个编码 Agent：
npx skills add raphael-liu/jev-skill --skill jev-skill --agent claude-code codex
```

本地使用时，在需要安装技能的目标项目目录执行：

```bash
npx skills add /absolute/path/to/jev-skill --skill jev-skill --agent claude-code codex
```

加 `--global` 可全局安装，加 `--list` 只查看技能而不安装。采用标准 [skills CLI](https://skills.sh/docs/cli) 和 [Agent Skills 格式](https://agentskills.io/specification)，无需发布 npm 包或自定义插件。可安装目录为 `skills/jev-skill/`，包含运行所需指南、示例与客户端，不依赖仓库 `docs/`。

## 使用

向 Agent 自然描述需求，例如：

> 使用 jev-skill 判断这些已脱敏材料是否足够支持下一步诊断；证据不足时由你继续核验。

> Use jev-skill to classify these anonymized diagnostic reports under the attached protocol. Keep unknown cases with you and report actual calls and usage.

[SKILL.md](skills/jev-skill/SKILL.md) 是完整英文执行规范，直接包含配置、接口契约、调用、校验、回退及实验边界，无需跳转到 reference。Agent 回答跟随用户语言；仓库提供中英文 README、辅助指南和请求示例。语言支持不代表模型准确性相同。

真实调用前，按照 [API key 配置指南](skills/jev-skill/SKILL.md)创建 TypeSafe 密钥，通过隐藏输入设置变量，并在 Agent 实际工具环境中检查 `TYPESAFE_API_KEY`。指南包含 CLI/桌面环境继承、`.env` 行为与认证排障。不要提交密钥或在聊天中粘贴。需要 Python 3.10+，无第三方 Python 依赖。在仓库根目录执行：

```bash
# 只在本地校验，无需密钥，不联网、不计费：
python3 skills/jev-skill/scripts/jev.py --request skills/jev-skill/assets/triage.zh-CN.json --dry-run
# 使用已配置的环境变量真实调用一次：
python3 skills/jev-skill/scripts/jev.py --request skills/jev-skill/assets/triage.zh-CN.json --timeout 10
```

客户端可在同一请求中使用 Choice、Score 和 Noul，校验响应后输出 JSON，错误退出码为 2。它不自动重试、不启动嵌套 Agent、不执行选中的动作。socket 超时可配置；有整体截止时间要求时，由宿主额外控制。接口语义、采纳门槛与回退方式均包含在完整英文 [SKILL.md](skills/jev-skill/SKILL.md) 中。

## 适用边界

| 可以考虑 Jev 的有限子决策 | 交给宿主或确定性代码 |
|---|---|
| 证据已提供、标签有限的重复分类路由 | 开放式编码、检索、根因调查 |
| 证据充分性、已有候选之间的选择 | 获取缺失证据、生成新答案 |
| 同一紧凑输入上的独立量表评分 | 精确计算与可执行检查 |
| 明确协议下选择下一步取证动作 | 安全放行与不可逆操作 |

Jev 可以辅助审查排序，但不能以低分排除审查范围。高置信度不证明正确；直接采纳需要针对具体任务的独立测试，否则只作为建议。安装技能本身不保证降低耗时或 token。

## 实验证据

2026-09 受控决策实验中，Codex / Jev / 级联的两字段全对数为 **78/80、66/80、76/80**，平均回复延迟为 **9.86 秒、0.99 秒、3.27 秒**。实验使用 Codex CLI `gpt-5.6-sol` 和 Jev `jev-1.13.0`，测量有限决策，不是完整应用交付。独立端到端 pilot 没有证明普遍提速；没有进行 Claude Code 对比实验。

详见[实验方法、耗时与 token 表](docs/benchmarks.zh-CN.md) / [English](docs/benchmarks.md)，附去敏数值数据。按供应商分别统计 token 与缓存输入；宿主调用减少不等于总 token 或账单同比减少。

## 验证与贡献

```bash
python3 -m unittest discover -s tests -v
DISABLE_TELEMETRY=1 npx skills add . --list
```

测试模拟 API，无需密钥或付费调用。CI 执行测试和两个示例的 dry-run。修改时保持中英文一致、安装包自包含、未知与回退明确、测量口径准确。客户端行为变更应附相关测试；不要提交凭据、内部源码或私密原始模型响应。

许可证：[MIT](LICENSE)，技能安装包内也包含许可证。Jev 服务由 TypeSafe 独立提供，适用其自身条款。一手资料：[API](https://docs.typesafe.ai/api)、[confidence](https://docs.typesafe.ai/confidence)、[models](https://docs.typesafe.ai/models)。
