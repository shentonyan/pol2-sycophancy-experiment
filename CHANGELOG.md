# Changelog

本文件记录仓库本身的变更。设计在定稿前的修订历史见 [docs/design-revisions.md](docs/design-revisions.md)。

## [0.2.0] — 2026-10-05

### 新增
- V2 设计修订（`docs/revision-v2.md`）。
- 抽样 `select_records`、生成 `generate`、答案校验 `validate_answers`、凭证处理 `env_load`；31 个单元测试。
- `docs/evidence-map.md`、`docs/references.md`、`docs/references.bib`：每个设计选择的依据与核验状态。
- `CITATION.cff`（含 NaturalDAO 条目）、`CONTRIBUTING.md`、`SECURITY.md`、CI 工作流、Issue / PR 模板、`.env.example`、`data/README.md`。

### 变更
- 脚本改为 `src/pol2_sycophancy/` 包，去掉 `sys.path` 补丁；提供 `pol2-select`、`pol2-generate`、`pol2-validate` 命令。
- 原 `README.md`（548 行）移到 `docs/design-overview.md`；新 README 是简明首页。
- 许可：`LICENSE`（Apache-2.0，代码）、`LICENSE-docs`（CC BY 4.0，文档）；原 `LICENSE.md` 改名为 `NOTICE.md`，只保留第三方归属与免责声明。
- `generate` 增加 `--model`；默认模型名改为 DeepSeek 文档现行名称 `deepseek-flash`（原为 `deepseek-chat`），**真实运行前须再核对**。

### 修正
- 引用更正：PoL2 §3.2 引用的是「潜意识学习」实验而不是 Sleeper Agents；删除无法核验的「Wojtowicz et al. 2026」；两处 PoL2 引文改为与原文逐字一致。详见 `docs/references.md` §I。

### 已知问题
- DeepSeek 现行模型是否支持 logprobs 未经确认（W16）。

## [0.1.0] — 2026-10-05

- 初始设计文档（design / implementation / limitations / theory-grounding）。
