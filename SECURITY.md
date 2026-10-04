# 安全政策

## 报告问题

如果发现密钥泄露、会把密钥写入日志或产物的缺陷，请**不要**公开提 Issue。请在 GitHub 仓库的 **Security** 标签页使用 *Report a vulnerability*（私密报告）。

## 范围

本仓库不提供在线服务。相关风险主要是：

- API 密钥进入日志、产物或提交（`env_load` 提供了脱敏过滤器与写入前扫描，见 `tests/test_env_load.py`）；
- 用户自行下载的数据集内容进入仓库（`.gitignore` 已排除 `data/` 与 `*.jsonl`）。

## 如果密钥已经提交

立即在 DeepSeek 控制台撤销该密钥并生成新密钥。只从 git 历史里删除并不足以让已泄露的密钥失效。
