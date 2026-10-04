#!/usr/bin/env python3
"""生成答案的验证（V2，见 docs/revision-v2.md §3.7），版本 validate-v1。

对每个生成的答案：
  * 没有被 max_tokens 截断；
  * 恰好一行 `ANSWER: (X)`，并且是最后一个非空行；
  * 该字母等于预期（对齐答案 = 数据集的 matching 选项，对立答案 = not-matching 选项）；
  * 不是拒绝；正文不过短。
对每一对：对齐答案与对立答案的字符长度比在 [0.8, 1.25] 内。

另外报告风格统计（长度、保留意见词比例），用来看两类答案是否在风格上系统性不同。

作为库使用（generate.py 调用），也可对冻结文件单独运行：
    python src/validate_answers.py --answers data/generated_answers.jsonl --out data/answer_validation.json
只用标准库。
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import sys
from pathlib import Path

VALIDATE_VERSION = "validate-v1"
RATIO_MIN, RATIO_MAX = 0.8, 1.25
MIN_BODY_CHARS = 20

ANSWER_LINE_RE = re.compile(r"(?im)^[ \t]*ANSWER[ \t]*:[ \t]*\(?([A-Z])\)?[ \t]*$")
REFUSAL_RE = re.compile(r"(?i)\b(i can't|i cannot|i'm unable|i am unable|as an ai|i won't|i will not)\b")
HEDGES = ("however", "although", "though", "might", "perhaps", "may ", "some ", "complex", "nuanced",
          "depends", "important to", "on the other hand", "it is worth", "to some extent")


def split_answer(text: str) -> tuple[str, str | None, list[str]]:
    """返回 (正文, ANSWER 行的字母, 问题代码列表)。正文不含 ANSWER 行。"""
    problems: list[str] = []
    matches = list(ANSWER_LINE_RE.finditer(text))
    if not matches:
        return text.strip(), None, ["no_answer_line"]
    if len(matches) > 1:
        problems.append("multiple_answer_lines")
    last = matches[-1]
    if text[last.end():].strip():
        problems.append("answer_line_not_last")
    return text[: matches[0].start()].strip(), last.group(1), problems


def check_answer(text: str, finish_reason: str | None, expected_letter: str) -> tuple[str, list[str]]:
    """返回 (正文, 失败代码列表)；空列表表示通过。"""
    body, letter, problems = split_answer(text)
    if finish_reason == "length":
        problems.append("truncated")
    if letter is not None and letter != expected_letter:
        problems.append("letter_mismatch")
    if REFUSAL_RE.search(body):
        problems.append("refusal")
    if len(body) < MIN_BODY_CHARS:
        problems.append("too_short")
    return body, problems


def length_ratio(aligned_body: str, opposed_body: str) -> float:
    return len(aligned_body) / max(1, len(opposed_body))


def ratio_ok(ratio: float) -> bool:
    return RATIO_MIN <= ratio <= RATIO_MAX


def word_count(text: str) -> int:
    return len(text.split())


def hedge_rate(text: str) -> float:
    """每 100 词里的保留意见词数。"""
    low = text.lower() + " "
    n = sum(low.count(h) for h in HEDGES)
    return 100.0 * n / max(1, word_count(text))


def style_stats(rows: list[dict]) -> dict:
    by_role: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r)
    out = {}
    for role, rs in sorted(by_role.items()):
        out[role] = {
            "n": len(rs),
            "mean_chars": round(statistics.fmean(len(r["body"]) for r in rs), 1),
            "mean_words": round(statistics.fmean(word_count(r["body"]) for r in rs), 1),
            "mean_hedges_per_100_words": round(statistics.fmean(hedge_rate(r["body"]) for r in rs), 2),
        }
    return out


def validate_file(rows: list[dict]) -> dict:
    """对冻结答案文件（每答案一行）做完整复核。"""
    by_rec: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for r in rows:
        by_rec[r["record_id"]][r["role"]] = r
    problems = collections.Counter()
    ratios, bad_records = [], []
    for rid, pair in sorted(by_rec.items()):
        if set(pair) != {"aligned", "opposed"}:
            problems["incomplete_pair"] += 1
            bad_records.append(rid)
            continue
        ok = True
        for role, r in pair.items():
            exp = r["expected_letter"]
            _, probs = check_answer(r["text"], r.get("finish_reason"), exp)
            for p in probs:
                problems[p] += 1
                ok = False
        ratio = length_ratio(pair["aligned"]["body"], pair["opposed"]["body"])
        ratios.append(ratio)
        if not ratio_ok(ratio):
            problems["length_ratio"] += 1
            ok = False
        if not ok:
            bad_records.append(rid)
    ratios.sort()
    return {
        "validate_version": VALIDATE_VERSION,
        "records": len(by_rec),
        "records_failing": len(bad_records),
        "problems": dict(sorted(problems.items())),
        "length_ratio_aligned_over_opposed": {
            "n": len(ratios),
            "min": round(ratios[0], 3) if ratios else None,
            "median": round(ratios[len(ratios) // 2], 3) if ratios else None,
            "max": round(ratios[-1], 3) if ratios else None,
        },
        "style": style_stats(rows),
        "failing_record_ids": bad_records[:50],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    rows = [json.loads(l) for l in args.answers.read_text(encoding="utf-8").splitlines() if l.strip()]
    report = validate_file(rows)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0 if report["records_failing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
