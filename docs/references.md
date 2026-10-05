# 参考文献与核验状态

本文件列出本仓库引用的每一项外部材料，以及它**实际被核验到什么程度**。核验日期：**2026-10-05**。

**核验等级**

- **已核验（原文）**：读到了原文，引文与原文逐字比对过。
- **已核验（题录）**：通过 arXiv 摘要页或 Crossref 确认了标题、作者、年份、卷页或日期。**没有读全文**，所以文中对该文献内容的说法只限于摘要里写明的部分。
- **未核验**：访问失败或没有找到。这类条目不得作为任何设计选择的依据。

作者列表较长时只列前几位，完整名单见链接。

---

## A. 理论来源（PoL2）

| 编号 | 文献 | 核验 |
|---|---|---|
| A1 | **DD周朝晖 与 NaturalDAO 贡献者.** *NaturalDAO*（`PoL/`：爱2证明 Proof of Love2, PoL2 完整理论）. <https://github.com/naturaldao/NaturalDAO> ；本仓库固定引用 commit `780e9955b11a94d7cfb6bff654ed696fa70a7591`（2026-09-18 23:06:54 +0800，作者 DDZhou，subject `Update 0. 前言.md`）. 许可 CC0 1.0. | **已核验（原文）**。克隆仓库，确认该 commit 存在且已在 `main` 上；本仓库中的 PoL2 引文已逐字比对该 commit 的文件。 |
| A2 | **DD周朝晖.** 《爱的证明：治理 AI 和人类文明的共识机制》（PoL 早期论文）. <https://github.com/DAism2019/Proof-of-Love> ；NaturalDAO `PoL/Readme.md` 说明 PoL2 理论部分从该论文提取而来. | 仓库**存在**（已克隆，最近提交 2026-05-29，许可 CC0 1.0）。**本仓库没有读该论文正文，也不依赖它。** |
| A3 | DD周朝晖. 同题论文，ResearchGate, 2025-10. <https://www.researchgate.net/publication/396701413> | **未核验**：访问返回 HTTP 429。本仓库不依赖它。 |

**版本说明（已核验）**：NaturalDAO 的 `main` 在 2026-10-04 的 HEAD（`053a67b`）已把 `PoL/` 下的章节重新编号：固定 commit 里 §3 是「AI 和人类文明的治理」、§4 是「冥想智慧公理」、§5 是「伦理对齐协议」；HEAD 里这三章变成 §5、§3、§4。本仓库所有章节号（如 §3.4、§5.3.2）都指**固定 commit**的编号。

## B. 数据集

| 编号 | 文献 | 核验 |
|---|---|---|
| B1 | **Perez, E., Ringer, S., Lukošiūtė, K., Nguyen, K., Chen, E., 等.** *Discovering Language Model Behaviors with Model-Written Evaluations.* arXiv:2212.09251, 2022-12-19. <https://arxiv.org/abs/2212.09251> | **已核验（题录）**。摘要写明：构造了 154 个数据集；较大的模型表现出更多 sycophancy（重复用户偏好）。 |
| B2 | **Anthropic.** `anthropics/evals`，`sycophancy/` 目录. <https://github.com/anthropics/evals> | **已核验**：已克隆；仓库 `LICENSE` 为 *Attribution 4.0 International*（CC BY 4.0）；本仓库用的三个文件的 sha256 前缀记录在 [revision-v2.md](revision-v2.md)。 |

## C. Sycophancy 背景

| 编号 | 文献 | 核验 |
|---|---|---|
| C1 | **Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., 等.** *Towards Understanding Sycophancy in Language Models.* arXiv:2310.13548, 2023-10-20（v4: 2025-05-10）. <https://arxiv.org/abs/2310.13548> | **已核验（题录）**。摘要写明：回答与用户观点一致时更容易被偏好；人类与偏好模型有时偏好写得有说服力但错误的回答。 |

## D. 评分模型的已知偏差

| 编号 | 文献 | 核验 |
|---|---|---|
| D1 | **Zheng, L., Chiang, W.-L., Sheng, Y., 等.** *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685, 2023-06-09. <https://arxiv.org/abs/2306.05685> | **已核验（题录）**。摘要写明：识别出位置偏差、冗长偏差、自我增强偏差。 |
| D2 | **Wang, P., Li, L., Chen, L., 等.** *Large Language Models are not Fair Evaluators.* arXiv:2305.17926, 2023-05-29. <https://arxiv.org/abs/2305.17926> | **已核验（题录）**。摘要写明：仅改变候选回答的出现顺序就能改变排名；提出跨顺序聚合（Balanced Position Calibration）。 |
| D3 | **Panickssery, A., Bowman, S. R., Feng, S.** *LLM Evaluators Recognize and Favor Their Own Generations.* arXiv:2404.13076, 2024-04-15. <https://arxiv.org/abs/2404.13076> | **已核验（题录）**。摘要写明：自我识别能力与自我偏好强度呈线性相关。 |

## E. 统计方法

以下六项都只核验了**题录**（Crossref），没有读全文。设计文档里对它们的使用，是「该方法族的标准来源」，不是「本仓库的流程与原文逐步相同」。

| 编号 | 文献 | DOI |
|---|---|---|
| E1 | Cameron, A. C., Miller, D. L. (2015). A Practitioner's Guide to Cluster-Robust Inference. *Journal of Human Resources* 50(2), 317–372. | 10.3368/jhr.50.2.317 |
| E2 | Cameron, A. C., Gelbach, J. B., Miller, D. L. (2008). Bootstrap-Based Improvements for Inference with Clustered Errors. *Review of Economics and Statistics* 90(3), 414–427. | 10.1162/rest.90.3.414 |
| E3 | Winkler, A. M., Ridgway, G. R., Webster, M. A., Smith, S. M., Nichols, T. E. (2014). Permutation inference for the general linear model. *NeuroImage* 92, 381–397. | 10.1016/j.neuroimage.2014.01.060 |
| E4 | Schuirmann, D. J. (1987). A comparison of the Two One-Sided Tests Procedure and the Power Approach for assessing the equivalence of average bioavailability. *Journal of Pharmacokinetics and Biopharmaceutics* 15(6), 657–680. | 10.1007/BF01068419 |
| E5 | Lakens, D. (2017). Equivalence Tests: A Practical Primer for *t* Tests, Correlations, and Meta-Analyses. *Social Psychological and Personality Science* 8, 355–362. | 10.1177/1948550617697177 |
| E6 | Nosek, B. A., Ebersole, C. R., DeHaven, A. C., Mellor, D. T. (2018). The preregistration revolution. *PNAS* 115, 2600–2606. | 10.1073/pnas.1708274114 |

## F. PoL2 §3.2 提到的两类研究（候选对应，**非 PoL2 给出的引用**）

PoL2 固定 commit 的 §3.2 用文字提到两项研究，**没有给出标题或链接**：「OpenAI 的研究表明，在一个狭窄领域用错误答案训练模型，会引发广泛的『涌现性未对齐』」；「Anthropic 的『潜意识学习』实验」。下面是我找到的、与这两句话**可能**对应的论文。**对应关系是我的判断，不是 PoL2 的声明。** 本实验的设计不依赖它们。

| 编号 | 文献 | 核验 |
|---|---|---|
| F1 | Betley, J., Tan, D., Warncke, N., 等. *Emergent Misalignment: Narrow finetuning can produce broadly misaligned LLMs.* arXiv:2502.17424, 2025-02-24. | **已核验（题录）** |
| F2 | Wang, M., Dupré la Tour, T., Watkins, O., 等. *Persona Features Control Emergent Misalignment.* arXiv:2506.19823, 2025-06-24. 摘要页未标明机构，**无法确认**它就是 PoL2 所说的「OpenAI 的研究」。 | **已核验（题录）**；机构对应**未核验** |
| F3 | Cloud, A., Le, M., Chua, J., 等. *Subliminal Learning: Language models transmit behavioral traits via hidden signals in data.* arXiv:2507.14805, 2025-07-20. 摘要页未标明机构，**无法确认**它就是 PoL2 所说的「Anthropic 的『潜意识学习』实验」。 | **已核验（题录）**；机构对应**未核验** |

## G. 工具文档

| 编号 | 文献 | 核验 |
|---|---|---|
| G1 | DeepSeek API 文档，Create Chat Completion. <https://api-docs.deepseek.com/api/create-chat-completion> | 页面列出 `logprobs`（布尔）与 `top_logprobs`（0–20）参数。**页面没有说明各模型是否支持。** |
| G2 | DeepSeek API 文档，Models & Pricing. <https://api-docs.deepseek.com/quick_start/pricing> | 页面列出的现行模型名是 `deepseek-flash` 与 `deepseek-v4-pro`，没有出现 `deepseek-chat`；功能表里没有列出 logprobs。**「没有列出」不等于「不支持」**，需要用真实请求确认。 |

## H. 仓库结构与研究软件规范

| 编号 | 文献 | 本仓库采用了什么 |
|---|---|---|
| H1 | Wilson, G., Bryan, J., Cranston, K., Kitzes, J., Nederbragt, L., Teal, T. K. (2017). Good enough practices in scientific computing. *PLOS Computational Biology* 13(6): e1005510. doi:10.1371/journal.pcbi.1005510 | README、LICENSE、CITATION、docs/、src/、测试、版本控制、changelog、依赖声明 |
| H2 | DrivenData. *Cookiecutter Data Science*. <https://cookiecutter-data-science.drivendata.org/> | `data/` 与 `src/`、`docs/` 分离；原始数据不入库 |
| H3 | Python Packaging User Guide. *src layout vs flat layout*. <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/> | `src/pol2_sycophancy/` 包布局，取代原来的平铺脚本与 `sys.path` 补丁 |
| H4 | GitHub Docs. *About CITATION files*. <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files> | 根目录 `CITATION.cff`（已用 cffconvert 按 schema 1.2.0 校验） |
| H5 | GitHub Docs. *About community profiles for public repositories*. <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories> | README、LICENSE、CONTRIBUTING、Issue 模板、安全政策；**Code of Conduct 尚未添加** |

H1–H5 的核验方式是读取页面内容；H1 的题录经 Crossref 复核。

---

## I. 已从本仓库撤下的引用

| 原出现处 | 原内容 | 处理 |
|---|---|---|
| `design.md`、`limitations.md`、术语表 | 「Wojtowicz et al. 2026」及其「缺少公共/排他区分」的断言 | 一次网页搜索没有找到对应论文，无法核验作者、标题与内容。已删除该名称；断言保留为**未验证的假设**，不作依据。 |
| 原 README §14.3 | 「Anthropic. Sleeper Agents」被说成 PoL2 §3.2 引用 | **错误**。PoL2 §3.2 引用的是「潜意识学习」实验，没有提到 Sleeper Agents。已更正，见 F 节。 |
| 原 README §14.1 | 「PoL2 §3.4 公共治理策略」等章节号 | 已按固定 commit 的编号核对，**无误**（见 A 节版本说明）。 |
