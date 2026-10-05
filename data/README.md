# data/

本目录的内容**不入库**（见 `.gitignore`），只保留这份说明。

## 需要的输入

从 <https://github.com/anthropics/evals>（`sycophancy/` 目录，CC BY 4.0）自行下载三个文件：

| 文件 | sha256 前缀（本设计审计所用） |
|---|---|
| `sycophancy_on_nlp_survey.jsonl` | `582860b42e2beec8` |
| `sycophancy_on_philpapers2020.jsonl` | `2f112b35334fbec0` |
| `sycophancy_on_political_typology_quiz.jsonl` | `691575571f659593` |

校验：`Get-FileHash <文件> -Algorithm SHA256`（PowerShell）。前缀不符说明数据集版本不同，抽样结果会不同。

## 本地产物

`pol2-select`、`pol2-generate` 会在此目录写入 `sample_*.jsonl`、`<split>/generated_answers.jsonl`、`*.sha256`、各类 `*_report.json`。这些都是可重新生成的，不入库。
