#!/usr/bin/env python3
"""聚类感知抽样（V2，见 docs/revision-v2.md §3.5）。

输入：anthropics/evals 的三个 sycophancy 文件所在目录。
输出（--out-dir）：
    sample_pilot.jsonl      先导样本
    sample_main.jsonl       主样本（聚类与先导不相交）
    selection_report.json   输入文件哈希、排除与去重计数、聚类与平衡情况、输出哈希

规则：
  * 只保留恰好 2 个选项的记录（NLP、political 全部；philpapers 取其 2 选项子集）。
  * 聚类单元 = 同一道「题」：NLP 取论断；political 取（选项前最后一句 + 选项集合）；
    philpapers 取（议题 + 选项集合）。
  * 按「选项之前的全部文字」去重（political 里有 600 组只是选项顺序对调的重复对）。
  * 先导与主样本的聚类互不相交；每个聚类最多取 m 条，按「对齐选项的文字」轮流取，使两种立场尽量均衡。
  * 全程用种子化的 random.Random(str)，同一 run_id 得到逐字节相同的输出。

只用标准库。
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import sys
from pathlib import Path

SELECT_VERSION = "select-v2"

SUBSET_FILES = {
    "nlp": "sycophancy_on_nlp_survey.jsonl",
    "pol": "sycophancy_on_political_typology_quiz.jsonl",
    "phil": "sycophancy_on_philpapers2020.jsonl",
}

OPTION_RE = re.compile(r"(?m)^\s*\(([A-Z])\)\s*(.*)$")
LETTER_RE = re.compile(r"\(([A-Z])\)")
NLP_CLAIM_RE = re.compile(r"as of 2022\?\s*(.*?)\s*\n\s*\nChoices:", re.S)
PHIL_TOPIC_RE = re.compile(r"following topic:\s*(.*?)\s*\n\s*\(A\)", re.S)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
TRAILING_ANSWER_RE = re.compile(r"\s*Answer:\s*$")


# ----------------------------------------------------------------- 解析 ----

def parse_options(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).strip()) for m in OPTION_RE.finditer(text)]


def pre_options_text(text: str) -> str:
    m = OPTION_RE.search(text)
    return text[: m.start()] if m else text


def letter_of(label: str) -> str | None:
    m = LETTER_RE.search(label or "")
    return m.group(1) if m else None


def cluster_key(subset: str, question: str, options: list[tuple[str, str]]) -> str | None:
    opt_set = " | ".join(sorted(o for _, o in options))
    if subset == "nlp":
        m = NLP_CLAIM_RE.search(question)
        return m.group(1).strip() if m else None
    if subset == "pol":
        pre = pre_options_text(question).strip()
        last = SENTENCE_SPLIT_RE.split(pre)[-1] if pre else ""
        return f"{last} || {opt_set}" if last else None
    if subset == "phil":
        m = PHIL_TOPIC_RE.search(question)
        return f"{m.group(1).strip()} || {opt_set}" if m else None
    raise ValueError(f"unknown subset {subset!r}")


def parse_record(subset: str, raw: dict, line_no: int) -> tuple[dict | None, str | None]:
    """返回 (记录, None) 或 (None, 排除原因)。"""
    question = raw["question"]
    options = parse_options(question)
    letters = sorted({l for l, _ in options})
    if len(letters) != 2:
        return None, "not_two_options"
    matching = letter_of(str(raw["answer_matching_behavior"]))
    nm_raw = raw["answer_not_matching_behavior"]
    nm_list = nm_raw if isinstance(nm_raw, list) else [nm_raw]
    nm_letters = [letter_of(str(x)) for x in nm_list]
    if matching is None or len(nm_letters) != 1 or nm_letters[0] is None:
        return None, "bad_label"
    opposed = nm_letters[0]
    if sorted({matching, opposed}) != letters:
        return None, "label_not_in_options"
    key = cluster_key(subset, question, options)
    if key is None:
        return None, "no_cluster_key"
    opt_map = dict(options)
    prompt_text = TRAILING_ANSWER_RE.sub("", question).rstrip()
    return {
        "record_id": hashlib.sha256(f"{subset}\n{question}".encode("utf-8")).hexdigest()[:16],
        "subset": subset,
        "cluster_id": f"{subset}-{hashlib.sha256(key.encode('utf-8')).hexdigest()[:8]}",
        "cluster_label": key[:120],
        "aligned_letter": matching,
        "opposed_letter": opposed,
        "aligned_text": opt_map[matching],
        "opposed_text": opt_map[opposed],
        "options": [[l, t] for l, t in options],
        "prompt_text": prompt_text,
        "user_affiliation": raw.get("user_affiliation"),
        "source_line": line_no,
        "_pre": pre_options_text(question),
    }, None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_subset(data_dir: Path, subset: str):
    path = data_dir / SUBSET_FILES[subset]
    if not path.is_file():
        raise SystemExit(f"找不到数据文件：{path}")
    records, excluded = [], collections.Counter()
    n_lines = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            n_lines += 1
            rec, why = parse_record(subset, json.loads(line), i)
            if rec is None:
                excluded[why] += 1
            else:
                records.append(rec)
    return path, n_lines, records, excluded


# ----------------------------------------------------------------- 抽样 ----

def rng_for(run_id: str, *parts: str) -> random.Random:
    return random.Random("|".join([run_id, SELECT_VERSION, *parts]))


def dedupe(records: list[dict], run_id: str) -> tuple[list[dict], int]:
    """按选项之前的文字去重；每组保留种子化排序后的第一条。"""
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in records:
        groups[r["_pre"]].append(r)
    kept, removed = [], 0
    for pre in sorted(groups):
        g = sorted(groups[pre], key=lambda r: r["record_id"])
        pick = rng_for(run_id, "dedupe", pre).choice(g)
        kept.append(pick)
        removed += len(g) - 1
    kept.sort(key=lambda r: (r["subset"], r["source_line"]))
    return kept, removed


def pick_in_cluster(recs: list[dict], m: int, run_id: str, cluster_id: str) -> list[dict]:
    """最多 m 条；按对齐选项的文字分组，轮流取，使各立场尽量均衡。"""
    rng = rng_for(run_id, "within", cluster_id)
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in sorted(recs, key=lambda r: r["record_id"]):
        groups[r["aligned_text"]].append(r)
    for k in groups:
        rng.shuffle(groups[k])
    order = sorted(groups)
    out: list[dict] = []
    while len(out) < m and any(groups[k] for k in order):
        for k in order:
            if groups[k] and len(out) < m:
                out.append(groups[k].pop())
    return out


def parse_counts(spec: str, subsets: list[str]) -> dict[str, int | None]:
    """'nlp=4,pol=3,phil=3' 或 'all'；None 表示「剩下的全部」。"""
    if spec.strip().lower() == "all":
        return {s: None for s in subsets}
    out: dict[str, int | None] = {s: 0 for s in subsets}
    for part in spec.split(","):
        k, v = part.split("=")
        k = k.strip()
        if k not in out:
            raise SystemExit(f"未知子集 {k!r}")
        out[k] = None if v.strip().lower() == "all" else int(v)
    return out


def select(by_subset: dict[str, list[dict]], run_id: str, pilot_clusters: dict, main_clusters: dict,
           pilot_m: int, main_m: int):
    pilot, main = [], []
    detail = {"pilot": {}, "main": {}}
    for subset, recs in by_subset.items():
        clusters: dict[str, list[dict]] = collections.defaultdict(list)
        for r in recs:
            clusters[r["cluster_id"]].append(r)
        ids = sorted(clusters)
        rng = rng_for(run_id, "clusters", subset)
        order = ids[:]
        rng.shuffle(order)
        kp = pilot_clusters.get(subset) or 0
        if kp > len(order):
            raise SystemExit(f"{subset}: 先导要 {kp} 个聚类，只有 {len(order)} 个")
        pilot_ids = order[:kp]
        rest = order[kp:]
        km = main_clusters.get(subset)
        km = len(rest) if km is None else km
        if km > len(rest):
            raise SystemExit(f"{subset}: 主样本要 {km} 个聚类，先导之后只剩 {len(rest)} 个")
        main_ids = rest[:km]
        for cid in sorted(pilot_ids):
            picked = pick_in_cluster(clusters[cid], pilot_m, run_id, cid)
            pilot.extend(picked)
            detail["pilot"][cid] = {"available": len(clusters[cid]), "picked": len(picked)}
        for cid in sorted(main_ids):
            picked = pick_in_cluster(clusters[cid], main_m, run_id, cid)
            main.extend(picked)
            detail["main"][cid] = {"available": len(clusters[cid]), "picked": len(picked)}
    return pilot, main, detail


def write_jsonl(path: Path, rows: list[dict]) -> str:
    data = "".join(json.dumps({k: v for k, v in r.items() if not k.startswith("_")},
                              ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    path.write_text(data, encoding="utf-8", newline="\n")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def summarize(rows: list[dict]) -> dict:
    by_subset = collections.Counter(r["subset"] for r in rows)
    clusters = collections.defaultdict(set)
    for r in rows:
        clusters[r["subset"]].add(r["cluster_id"])
    aligned = collections.defaultdict(collections.Counter)
    for r in rows:
        aligned[r["cluster_id"]][r["aligned_text"]] += 1
    imbalanced = sum(1 for c in aligned.values() if len(c) > 1 and max(c.values()) - min(c.values()) > 1)
    affil = collections.Counter(r["user_affiliation"] for r in rows if r["user_affiliation"])
    return {
        "records": len(rows),
        "records_by_subset": dict(sorted(by_subset.items())),
        "clusters_by_subset": {k: len(v) for k, v in sorted(clusters.items())},
        "clusters_with_imbalance_gt1": imbalanced,
        "political_affiliation": dict(sorted(affil.items())),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, type=Path, help="含三个 sycophancy_*.jsonl 的目录")
    ap.add_argument("--run-id", required=True, help="运行标识，决定全部种子；预注册时固定")
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    ap.add_argument("--subsets", default="nlp,pol,phil", help="逗号分隔，默认三个都用")
    ap.add_argument("--pilot-clusters", default="nlp=4,pol=3,phil=3")
    ap.add_argument("--pilot-per-cluster", type=int, default=4)
    ap.add_argument("--main-clusters", default="all", help="'all' = 先导之后剩下的全部；或 nlp=20,pol=10,phil=40")
    ap.add_argument("--main-per-cluster", type=int, default=3)
    args = ap.parse_args(argv)

    subsets = [s.strip() for s in args.subsets.split(",") if s.strip()]
    for s in subsets:
        if s not in SUBSET_FILES:
            raise SystemExit(f"未知子集 {s!r}")
    pilot_k = parse_counts(args.pilot_clusters, subsets)
    main_k = parse_counts(args.main_clusters, subsets)

    report: dict = {
        "select_version": SELECT_VERSION,
        "run_id": args.run_id,
        "seed_scheme": "random.Random('<run_id>|select-v2|<purpose>|<key>')",
        "params": {"subsets": subsets, "pilot_clusters": pilot_k, "pilot_per_cluster": args.pilot_per_cluster,
                   "main_clusters": main_k, "main_per_cluster": args.main_per_cluster},
        "inputs": {}, "loaded": {}, "excluded": {}, "duplicates_removed": {}, "clusters_available": {},
    }
    by_subset: dict[str, list[dict]] = {}
    for s in subsets:
        path, n_lines, recs, excluded = load_subset(args.data_dir, s)
        recs, removed = dedupe(recs, args.run_id)
        by_subset[s] = recs
        report["inputs"][s] = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        report["loaded"][s] = n_lines
        report["excluded"][s] = dict(sorted(excluded.items()))
        report["duplicates_removed"][s] = removed
        report["clusters_available"][s] = len({r["cluster_id"] for r in recs})

    pilot, main_rows, detail = select(by_subset, args.run_id, pilot_k, main_k,
                                      args.pilot_per_cluster, args.main_per_cluster)
    pilot_ids = {r["cluster_id"] for r in pilot}
    main_ids = {r["cluster_id"] for r in main_rows}
    if pilot_ids & main_ids:
        raise SystemExit("内部错误：先导与主样本聚类相交")
    if {r["record_id"] for r in pilot} & {r["record_id"] for r in main_rows}:
        raise SystemExit("内部错误：先导与主样本记录相交")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report["outputs"] = {
        "sample_pilot.jsonl": write_jsonl(args.out_dir / "sample_pilot.jsonl", pilot),
        "sample_main.jsonl": write_jsonl(args.out_dir / "sample_main.jsonl", main_rows),
    }
    report["pilot"] = summarize(pilot)
    report["main"] = summarize(main_rows)
    requested = {"pilot": args.pilot_per_cluster, "main": args.main_per_cluster}
    report["shortfalls"] = {split: {c: d for c, d in detail[split].items() if d["picked"] < requested[split]}
                            for split in detail}
    (args.out_dir / "selection_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print(f"先导：{report['pilot']['records']} 条，聚类 {report['pilot']['clusters_by_subset']}")
    print(f"主样本：{report['main']['records']} 条，聚类 {report['main']['clusters_by_subset']}")
    print(f"去重移除：{report['duplicates_removed']}；排除：{report['excluded']}")
    print(f"报告：{args.out_dir / 'selection_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
