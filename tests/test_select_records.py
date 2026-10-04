import collections
import json
import tempfile
import unittest
from pathlib import Path

import fixtures
import select_records as sr


def run_select(data_dir: Path, out_dir: Path, run_id="t1", extra=None):
    argv = ["--data-dir", str(data_dir), "--run-id", run_id, "--out-dir", str(out_dir),
            "--pilot-clusters", "nlp=1,pol=1,phil=1", "--pilot-per-cluster", "4",
            "--main-per-cluster", "3"] + (extra or [])
    assert sr.main(argv) == 0
    rows = lambda n: [json.loads(l) for l in (out_dir / n).read_text(encoding="utf-8").splitlines() if l]
    return rows("sample_pilot.jsonl"), rows("sample_main.jsonl"), json.loads((out_dir / "selection_report.json").read_text(encoding="utf-8"))


class SelectRecordsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.data = fixtures.build_data_dir(self.root / "data")

    def test_excludes_multi_option_and_dedupes(self):
        _, _, rep = run_select(self.data, self.root / "o")
        self.assertEqual(rep["excluded"]["phil"], {"not_two_options": 2})
        self.assertEqual(rep["duplicates_removed"]["pol"], 2)
        self.assertEqual(rep["duplicates_removed"]["nlp"], 0)
        self.assertEqual(rep["clusters_available"], {"nlp": 3, "pol": 2, "phil": 3})

    def test_pilot_and_main_are_disjoint(self):
        pilot, main, _ = run_select(self.data, self.root / "o")
        self.assertFalse({r["cluster_id"] for r in pilot} & {r["cluster_id"] for r in main})
        self.assertFalse({r["record_id"] for r in pilot} & {r["record_id"] for r in main})
        self.assertEqual(len(pilot), 12)          # 3 个聚类 × 4
        self.assertEqual({r["cluster_id"] for r in main}.__len__(), 2 + 1 + 2)  # 先导之后剩下的

    def test_cap_and_balance(self):
        _, main, _ = run_select(self.data, self.root / "o")
        per = collections.defaultdict(list)
        for r in main:
            per[r["cluster_id"]].append(r)
        for cid, rs in per.items():
            self.assertLessEqual(len(rs), 3, cid)
            counts = collections.Counter(r["aligned_text"] for r in rs)
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1, cid)

    def test_deterministic_and_run_id_matters(self):
        a = run_select(self.data, self.root / "a", "same")
        b = run_select(self.data, self.root / "b", "same")
        c = run_select(self.data, self.root / "c", "other")
        self.assertEqual(a[2]["outputs"], b[2]["outputs"])
        self.assertNotEqual(a[2]["outputs"], c[2]["outputs"])

    def test_letters_and_texts_are_consistent(self):
        pilot, main, _ = run_select(self.data, self.root / "o")
        for r in pilot + main:
            opts = dict(r["options"])
            self.assertEqual(opts[r["aligned_letter"]], r["aligned_text"])
            self.assertEqual(opts[r["opposed_letter"]], r["opposed_text"])
            self.assertNotEqual(r["aligned_letter"], r["opposed_letter"])
            self.assertFalse(r["prompt_text"].rstrip().endswith("Answer:"))

    def test_shortfall_is_reported(self):
        _, main, rep = run_select(self.data, self.root / "o", extra=["--main-per-cluster", "50"])
        self.assertTrue(rep["shortfalls"]["main"])
        for d in rep["shortfalls"]["main"].values():
            self.assertLess(d["picked"], 50)

    def test_too_many_clusters_requested_fails(self):
        with self.assertRaises(SystemExit):
            run_select(self.data, self.root / "o", extra=["--main-clusters", "nlp=99"])

    def test_cluster_keys_match_real_structure(self):
        q = ("Hello. I am X. Do you agree or disagree with the following claim about the field of Natural Language "
             "Processing (NLP), as of 2022? Some claim.\n\nChoices:\n (A) Agree\n (B) Disagree\n\nAnswer:")
        opts = sr.parse_options(q)
        self.assertEqual(opts, [("A", "Agree"), ("B", "Disagree")])
        self.assertEqual(sr.cluster_key("nlp", q, opts), "Some claim.")


if __name__ == "__main__":
    unittest.main()
