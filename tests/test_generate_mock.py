import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import fixtures
import generate as gen
import select_records as sr
import validate_answers as va


def make_sample(root: Path) -> tuple[Path, list[dict]]:
    data = fixtures.build_data_dir(root / "data")
    out = root / "sel"
    assert sr.main(["--data-dir", str(data), "--run-id", "g1", "--out-dir", str(out),
                    "--pilot-clusters", "nlp=2,pol=1,phil=2", "--pilot-per-cluster", "4"]) == 0
    recs = [json.loads(l) for l in (out / "sample_pilot.jsonl").read_text(encoding="utf-8").splitlines() if l]
    return out, recs


def big_budget(n):
    return gen.Budget(max_calls=10 * n, max_prompt_tokens=10**9, max_completion_tokens=10**9)


class GenerateMockTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.sel, self.recs = make_sample(self.root)

    def run_gen(self, client, budget=None, name="o"):
        out = self.root / name
        code = gen.run(self.recs, client, budget or big_budget(len(self.recs)), out, workers=3, secrets=[], extra_report={})
        rows = [json.loads(l) for l in (out / "generated_answers.jsonl").read_text(encoding="utf-8").splitlines() if l]
        rep = json.loads((out / "generation_report.json").read_text(encoding="utf-8"))
        return code, out, rows, rep

    def test_clean_run_freezes_two_rows_per_record(self):
        code, out, rows, rep = self.run_gen(gen.MockClient())
        self.assertEqual(code, 0)
        self.assertEqual(len(rows), 2 * len(self.recs))
        self.assertEqual(rep["records_valid"], len(self.recs))
        self.assertEqual(rep["status"], "COMPLETE")
        digest = hashlib.sha256((out / "generated_answers.jsonl").read_bytes()).hexdigest()
        self.assertEqual((out / "generated_answers.sha256").read_text().split()[0], digest)
        self.assertEqual(va.validate_file(rows)["records_failing"], 0)
        by = {(r["record_id"], r["role"]): r for r in rows}
        for rec in self.recs:
            self.assertEqual(by[(rec["record_id"], "aligned")]["expected_letter"], rec["aligned_letter"])
            self.assertEqual(by[(rec["record_id"], "opposed")]["expected_letter"], rec["opposed_letter"])
            self.assertEqual(by[(rec["record_id"], "aligned")]["answer_id"], "A1")
            self.assertEqual(by[(rec["record_id"], "opposed")]["answer_id"], "A2")

    def test_retry_repairs_transient_faults(self):
        faults = {"wrong_letter": 0.5, "no_answer_line": 0.3, "long": 0.5, "truncate": 0.2}
        code, out, rows, rep = self.run_gen(gen.MockClient(faults))
        self.assertEqual(code, 0)
        self.assertGreater(rep["retries_total"], 0)
        self.assertEqual(rep["records_valid"] + sum(rep["records_excluded"].values()), len(self.recs))
        self.assertEqual(len(rows), 2 * rep["records_valid"])
        # 每个角色最多重试一次：如果较长的那个答案已经因为格式问题用掉了重试，长度比问题就不再修，
        # 记录按 length_ratio 排除。除此之外，非持续性错误一次重试都能修好。
        self.assertLessEqual(set(rep["records_excluded"]), {"length_ratio"})
        self.assertGreater(rep["records_valid"], len(self.recs) // 2)
        self.assertEqual(va.validate_file(rows)["records_failing"], 0)

    def test_persistent_faults_are_excluded_and_counted(self):
        code, out, rows, rep = self.run_gen(gen.MockClient({"wrong_letter": 1.0}, persistent=True))
        self.assertEqual(code, 0)
        self.assertEqual(rep["records_valid"], 0)
        self.assertEqual(rep["records_excluded"], {"letter_mismatch": len(self.recs)})
        self.assertEqual(rows, [])

    def test_persistent_length_mismatch_is_excluded(self):
        code, out, rows, rep = self.run_gen(gen.MockClient({"long": 1.0}, persistent=True))
        self.assertEqual(rep["records_valid"] + sum(rep["records_excluded"].values()), len(self.recs))
        self.assertEqual(va.validate_file(rows)["records_failing"], 0)   # 留下的都合格

    def test_budget_cap_stops_and_marks_run(self):
        code, out, rows, rep = self.run_gen(gen.MockClient(), budget=gen.Budget(5, 10**9, 10**9))
        self.assertEqual(rep["status"], "SPEND-CAPPED")
        self.assertLessEqual(rep["calls"], 5)
        self.assertGreater(rep["records_excluded"].get("budget_stop", 0), 0)
        self.assertEqual(len(rows), 2 * rep["records_valid"])

    def test_api_failures_are_counted(self):
        code, out, rows, rep = self.run_gen(gen.MockClient({"api_failure": 1.0}, persistent=True))
        self.assertGreater(rep["api_failures"], 0)
        self.assertEqual(rep["records_valid"], 0)

    def test_prompts_do_not_leak_condition_or_stance_words(self):
        for rec in self.recs[:5]:
            for role in ("aligned", "opposed"):
                p = gen.build_prompt(rec, role).lower()
                for word in ("sycophan", "flatter", "agree with the person", "please the user", "fair to"):
                    self.assertNotIn(word, p)

    def test_aligned_and_opposed_prompts_differ_only_in_option(self):
        rec = self.recs[0]
        a, o = gen.build_prompt(rec, "aligned"), gen.build_prompt(rec, "opposed")
        a2 = a.replace(f'"{rec["aligned_text"]}" (option {rec["aligned_letter"]})', "<OPT>").replace(
            f'ANSWER: ({rec["aligned_letter"]})', "ANSWER: (<L>)")
        o2 = o.replace(f'"{rec["opposed_text"]}" (option {rec["opposed_letter"]})', "<OPT>").replace(
            f'ANSWER: ({rec["opposed_letter"]})', "ANSWER: (<L>)")
        self.assertEqual(a2, o2)

    def test_secret_in_output_aborts(self):
        class Leaky(gen.MockClient):
            def complete(self, prompt, max_tokens, temperature):
                res = super().complete(prompt, max_tokens, temperature)
                res["text"] = "sk-" + "A" * 30 + "\n" + res["text"]
                return res
        with self.assertRaises(SystemExit):
            self.run_gen(Leaky(), name="leak")

    def test_cli_mock_smoke_and_overwrite_guard(self):
        argv = ["--split", "pilot", "--data-dir", str(self.sel), "--mock", "--limit", "6"]
        self.assertEqual(gen.main(argv), 0)
        with self.assertRaises(SystemExit):
            gen.main(argv)                      # 已有输出，未加 --force
        self.assertEqual(gen.main(argv + ["--force"]), 0)


if __name__ == "__main__":
    unittest.main()
