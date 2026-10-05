# 贡献指南

欢迎提 Issue 与 PR。这是一个预注册实验，所以有几条额外的纪律。

## 开发环境

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[api]"
python -m unittest discover -s tests
```

测试用合成数据，不联网，不调用 API。PR 必须保持测试通过。

## 引用纪律

- 新增或修改任何文献引用，必须同时更新 `docs/references.md`，并写明核验方式（读了原文 / 只核验题录 / 未核验）。
- **不得凭记忆写作者、标题、年份、DOI、页码或引文。** 查不到就标「未核验」，不要补全。
- 引用 PoL2 原文必须逐字，并标明固定 commit 的章节号。
- 新增设计选择必须在 `docs/evidence-map.md` 中登记依据类型；没有外部依据就写「自定」。

## 预注册后的纪律

`prereg-v1` 标签之后，不得修改已预注册的分析计划、样本冻结规则与检验设定。需要改动时，新增一个带日期的偏离说明，不要覆盖原文。

## 数据与密钥

- `data/`、`.env`、任何 `*.jsonl` 不入库。
- 提交前确认 diff 中没有 API key。
- 不要在 Issue 或 PR 里贴数据集原文或密钥。

## 提交信息

一句话说明改了什么、为什么。

## 许可

提交即同意：代码按 Apache-2.0，文档按 CC BY 4.0 授权。
