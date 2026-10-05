# 谄媚的第三方条件测试

**The Third-Party Condition Test for Sycophancy**

一个把 PoL2（爱2证明）理论中「爱＝公共性 / 恨＝排他性私有」的对立，转成**可测量实验假设**的设计与实现。

> 当评分模型被要求考虑一个**不在场、且不共享当事人立场**的第三方时，它对「顺从当事人立场」的答案的偏好，是否下降？

[![CI](https://github.com/shentonyan/pol2-sycophancy-experiment/actions/workflows/ci.yml/badge.svg)](https://github.com/shentonyan/pol2-sycophancy-experiment/actions/workflows/ci.yml)
![license](https://img.shields.io/badge/code-Apache--2.0-blue)
![license](https://img.shields.io/badge/docs-CC--BY--4.0-lightgrey)

## 状态（2026-10-05）

| 阶段 | 状态 |
|---|---|
| 实验设计（V2） | 已采纳，见 [docs/revision-v2.md](docs/revision-v2.md) |
| 抽样 / 生成 / 答案校验 脚本 | 已实现，31 个单元测试通过；生成脚本只用模拟客户端跑过 |
| 评分 / 抽取 / 分析 / 报告 脚本 | 未实现 |
| 预注册、先导、主实验 | 未开始 |

**目前没有任何实验结果。** 本仓库不声称验证或证伪了 PoL2。

## 理论来源

本实验的理论动机来自 **PoL2（爱2证明, Proof of Love2）**，由 **DD周朝晖** 原创提出，发布在 NaturalDAO 仓库：

- **NaturalDAO** — <https://github.com/naturaldao/NaturalDAO>（理论正文在 [`PoL/`](https://github.com/naturaldao/NaturalDAO/tree/main/PoL)）
- 本仓库固定引用的版本：commit [`780e9955b11a94d7cfb6bff654ed696fa70a7591`](https://github.com/naturaldao/NaturalDAO/tree/780e9955b11a94d7cfb6bff654ed696fa70a7591/PoL)（2026-09-18）
- PoL 早期论文：<https://github.com/DAism2019/Proof-of-Love>

本仓库是**下游工程测量**，不是 PoL2 理论的一部分，也不代表其官方立场。理论文字与实验操作化的逐句对应见 [docs/theory-grounding.md](docs/theory-grounding.md)。

## 快速开始

需要 Python ≥ 3.11。核心代码只用标准库；真实调用 API 才需要 `openai`。

```powershell
git clone https://github.com/shentonyan/pol2-sycophancy-experiment.git
cd pol2-sycophancy-experiment
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[api]"

# 测试（无网络、无 API 调用）
python -m unittest discover -s tests

# 抽样（数据集需自行下载，见 data/README.md）
pol2-select --data-dir <含三个 sycophancy_*.jsonl 的目录> --run-id <RUN_ID> --out-dir data

# 用模拟客户端检查生成流程（不调用 API）
pol2-generate --split pilot --mock --mock-fault-rate 0.15
```

真实生成需要把 `.env.example` 复制为 `.env` 并填入 `DEEPSEEK_API_KEY`。默认模型名与 logprobs 支持情况**尚未核实**，见 [docs/limitations.md](docs/limitations.md) 的 W15、W16。

## 仓库结构

```
.
├── README.md
├── CITATION.cff               如何引用本仓库（含 NaturalDAO 条目）
├── CHANGELOG.md
├── CONTRIBUTING.md  SECURITY.md
├── LICENSE                    代码：Apache-2.0
├── LICENSE-docs               文档与设计：CC BY 4.0
├── NOTICE.md                  第三方材料的归属与免责声明
├── pyproject.toml
├── .env.example
├── src/pol2_sycophancy/       实现（env_load / select_records / generate / validate_answers）
├── tests/                     单元测试（合成数据，不含真实数据集）
├── data/                      本地数据（不入库），见 data/README.md
├── docs/
│   ├── design-overview.md     原 README：设计总览（V1，部分被 V2 取代）
│   ├── revision-v2.md         V2 修订（以此为准）
│   ├── design.md  implementation.md  limitations.md
│   ├── theory-grounding.md    PoL2 原文与实验操作化的对应
│   ├── pol2-terminology.md    PoL2 术语表
│   ├── evidence-map.md        每个设计选择 → 依据的文献（或「无外部依据」）
│   ├── references.md          参考文献与核验状态
│   ├── references.bib
│   ├── design-revisions.md    设计定稿前的修订记录
│   └── provenance.md          设计产出过程（去标识化）
└── .github/                   CI、Issue / PR 模板
```

这个布局参考了科研软件的公开规范，依据见 [docs/references.md](docs/references.md) §H。

## 文档阅读顺序

1. [docs/revision-v2.md](docs/revision-v2.md)：当前有效的设计决定
2. [docs/design-overview.md](docs/design-overview.md)：背景与完整设计（与 V2 冲突处以 V2 为准）
3. [docs/evidence-map.md](docs/evidence-map.md)：每个选择的依据，以及哪些选择**没有**外部依据
4. [docs/limitations.md](docs/limitations.md)：已声明的限制

## 引用

见 [CITATION.cff](CITATION.cff)。使用 PoL2 理论时请同时引用 NaturalDAO 原仓库。

## 许可

代码 Apache-2.0（[LICENSE](LICENSE)）；文档与设计 CC BY 4.0（[LICENSE-docs](LICENSE-docs)）。PoL2 理论材料与 Anthropic 数据集的权利归各自作者，见 [NOTICE.md](NOTICE.md)。
