# 实施计划

技术栈：**Python 3.11，标准库 + `openai` 包**。
统计**全部**用标准库实现（`math.comb`），**不引入 scipy** —— 使任何一步都可被独立复算。

---

## 1. 脚本职责与运行顺序

### `src/env_load.py` — 凭证与脱敏

- 显式读取 profile `.env`（**绝不**依赖继承环境——H3 已实测 `os.environ` 中键不存在）
- 要求 `DEEPSEEK_API_KEY` 非空；缺失或为空 → `SystemExit(2)` 并给出清晰信息
- 导出 `DEEPSEEK_BASE_URL`，默认 `https://api.deepseek.com`
- 安装 **logger 脱敏过滤器**，使键值**永不**到达日志或工件
- 只记录键的**存在性与长度**，从不记录值

### `src/select_records.py` — 抽样

- 加载三个 JSONL
- 用 `re.findall(r"\(([A-Z])\)")` 取 `len(set(...))` 解析选项数
- 施加冻结分层与种子 `sha256(run_id || 'candidate-B')`
- 产出 `sample_main.jsonl` 与 `sample_pilot.jsonl`（**不相交**）
- 产出选择报告：排除记录计数与原因

### `src/generate.py` — 生成与冻结

- 每条记录构造**两个**生成提示（立场对齐槽、立场对立槽）
- 发出**两次**调用/记录（**C2**），`temperature=0.0`、`max_tokens=320`、5 次指数退避
- 施加预注册的槽位→字母匿名化
- 写 `data/generated_answers.jsonl`，**每答案一行**（每记录 2 行：`A1`、`A2`）
- 记录 `finish_reason`，标记 `finish_reason == 'length'` 的记录
- **断言**行数 `== 2 × 成功生成记录数`，不符即**中止**
- 写 `data/generated_answers.sha256`

### `src/score.py` — 评分

- **先校验** `sha256(generated_answers.jsonl)` 与记录的摘要，不符即中止
- 每条记录、每个 $r \in [0, R)$：从**同一冻结答案集**构造 A/B（及 B0/C，若启用）
- 运行机械差异断言：`A.replace(A_suffix,"") == B.replace(B_suffix,"")`，并对 B0/C 做同样两两断言
- 调用 `deepseek-chat`，`temperature=0.0`、`max_tokens=400`、5 次退避
- 追加一行/调用到 `data/completion_log.jsonl`，字段：

```
run_id, subset, record_sha256, condition, repeat_index,
slot_letter_map, raw_text, finish_reason,
prompt_tokens, completion_tokens, request_id,
attempt_count, error, timestamp_utc
```

- **每次调用前**递增总调用计数器；依据上一调用返回的 usage 递增 prompt/completion token 计数器；**任一**上限触达即停止发放新调用

### `src/extract.py` — 抽取

- 按 `extract-v1` 七步规则解析保存的原始文本
- 产出六桶计数：`decision_1` / `tie` / `unparseable` / `format_violation` / `refused` / `api_failure`
- 拒绝正则优先于可解析性

### `src/pilot_sizing.py` — 先导定规模

- 用先导实测方差，对**真实的聚类置换检验**做 Monte-Carlo 模拟
- 输出 `sizing.json`：$N_{\mathrm{main}}$、$R$、模拟功效、B0 达成的长度匹配比
- **硬闸门**：主运行被阻塞在 `sizing.json` 存在且与预注册一致上

### `src/analyze.py` — 分析

- 聚类置换检验（主 $p$ 值，10,000 次，种子化）
- 精确双侧符号检验（补充，`math.comb`）
- 稳定性报告（逐记录 + 聚合）
- B0 解读规则裁决
- **两方法符号不一致 → 报告 `unresolved`**

### `src/report.py` — 报告

- 渲染含**两个强制绑定句**的报告：
  1. 构造收窄句（与任何 $\hat\delta$/SSR 陈述**同段**）
  2. 完整绑定表头（两句，均具约束力）
- 报告全部桶计数、稳定性、位置偏置诊断、子集分解（标记为探索性）

---

## 2. 安全与凭证

| 要求 | 实现 |
|---|---|
| 密钥只从 profile `.env` 读取 | `env_load.py` 显式 source，不依赖继承环境 |
| 密钥永不回显 | logger 脱敏过滤器（**第二道**防线） |
| 密钥永不进工件 | 写入前扫描字面键值与 `sk-[A-Za-z0-9]{20,}` 模式，命中即中止写入 |
| 只读对待非自有系统 | 无 push / PR / issue / comment / fork-with-content |
| 无真实可识别个人数据进入任何持久存储 | 不采集、不存储 |

---

## 3. 依赖

```
openai>=1.0
```

其余全部为 **Python 3.11 标准库**：`json`、`re`、`math`、`hashlib`、`random`、`collections`、`csv`、`logging`、`os`、`sys`、`time`、`decimal`。

**明确不引入**：`scipy`、`numpy`、`pandas`、`statsmodels`。

> 理由：实验的全部统计必须能被第三方工程师用标准库独立复算。引入 scipy 会让「复算」变成「信任」。

---

## 4. 运行顺序

```bash
# 0. 环境
python src/env_load.py                 # 校验凭证，失败即退出

# 1. 抽样
python src/select_records.py           # → sample_main.jsonl, sample_pilot.jsonl

# 2. 先导（40 × 3）
python src/generate.py  --split pilot
python src/score.py     --split pilot
python src/extract.py   --split pilot

# 3. 定规模 → 写入预注册（硬闸门）
python src/pilot_sizing.py             # → sizing.json

# 4. 主运行（不得早于上一步的哈希）
python src/generate.py  --split main
python src/score.py     --split main
python src/extract.py   --split main

# 5. 分析
python src/analyze.py

# 6. 报告
python src/report.py                   # → report.md
```

---

## 5. 预算上限的机械执行

```
MAX_CALLS          = 7000
MAX_PROMPT_TOKENS  = 1_500_000
MAX_COMPLETION_TOKENS = 700_000
```

`score.py` 在**每次**调用**之前**检查三个计数器。任一触达即：

1. 停止发放新调用
2. 将运行标注为 **`SPEND-CAPPED`**
3. 若稳定性闸门因此未能通过，报告闸门**失败**而非放宽它

美元数字**不参与**任何控制逻辑，仅作为非承重说明。

---

## 6. 可复算性要求

给定：
- 冻结的答案文件
- 冻结的补全日志（每调用一行，含原始文本）
- 解析器版本字符串 `extract-v1`

**另一位工程师**应当能仅用 `json` + `re` + `collections`（标准库）复算：
- 每一个桶计数
- 每一个稳定性数字
- $\hat\delta$、SSR 及其区间
- 两个 $p$ 值

**无需模型访问，无需参照本仓库代码。** 这是验收标准之一。

---

## 7. 待实现清单

| 状态 | 项 |
|---|---|
| ⬜ | `src/env_load.py` |
| ⬜ | `src/select_records.py` |
| ⬜ | `src/generate.py` |
| ⬜ | `src/score.py` |
| ⬜ | `src/extract.py` |
| ⬜ | `src/pilot_sizing.py` |
| ⬜ | `src/analyze.py` |
| ⬜ | `src/report.py` |
| ⬜ | `pilot/` 先导运行与定规模 |
| ⬜ | 预注册工件（`prereg.yaml` + 哈希） |
| ⬜ | 主运行 |
| ⬜ | 分析报告 |

> **当前状态**：本仓库交付的是**设计与实施计划**。上述脚本**尚未实现**，主实验**尚未运行**，因此**没有任何实验结果**。这一点被明确声明，而非留白不表。

---

## 8. 交付边界（能力外事项）

| 事项 | 状态 |
|---|---|
| 联系理论作者或数据集作者 | **NOT_A_CAPABILITY** —— 无已验证外发路径；且属研究者本人的外部行为 |
| 投稿或发表 | **NOT_A_CAPABILITY** —— 同上 |
| 取得的早期 PoL 论文全文 | **未获取** —— 存在但未获授权读取；因此不主张任何「最新版本」的超越性断言 |
| 2026 年论文全文 | **未获取** —— 因此相关断言标记为 UNVERIFIED |
