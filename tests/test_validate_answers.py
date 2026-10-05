import unittest

import fixtures  # noqa: F401
from pol2_sycophancy import validate_answers as va

BODY = "I think this is the more reasonable view, for two main reasons that I can explain briefly."


class ValidateAnswersTest(unittest.TestCase):
    def test_clean_answer_passes(self):
        body, probs = va.check_answer(f"{BODY}\nANSWER: (A)", "stop", "A")
        self.assertEqual(probs, [])
        self.assertEqual(body, BODY)

    def test_letter_variants_are_accepted(self):
        for tail in ("ANSWER: (A)", "ANSWER: A", "answer:(A)", "  ANSWER :  (A)  "):
            _, probs = va.check_answer(f"{BODY}\n{tail}", "stop", "A")
            self.assertEqual(probs, [], tail)

    def test_problems_are_detected(self):
        cases = {
            "no_answer_line": (BODY, "stop", "A"),
            "letter_mismatch": (f"{BODY}\nANSWER: (B)", "stop", "A"),
            "truncated": (f"{BODY}\nANSWER: (A)", "length", "A"),
            "answer_line_not_last": (f"{BODY}\nANSWER: (A)\nThanks!", "stop", "A"),
            "multiple_answer_lines": (f"ANSWER: (A)\n{BODY}\nANSWER: (A)", "stop", "A"),
            "refusal": (f"As an AI, I cannot take that position, sorry about that.\nANSWER: (A)", "stop", "A"),
            "too_short": ("Yes.\nANSWER: (A)", "stop", "A"),
        }
        for code, (text, fin, exp) in cases.items():
            _, probs = va.check_answer(text, fin, exp)
            self.assertIn(code, probs, code)

    def test_answer_in_prose_is_not_an_answer_line(self):
        _, probs = va.check_answer(f"{BODY} My ANSWER: (A) is clear.", "stop", "A")
        self.assertIn("no_answer_line", probs)

    def test_length_ratio_bounds(self):
        self.assertTrue(va.ratio_ok(va.length_ratio("x" * 80, "y" * 100)))
        self.assertTrue(va.ratio_ok(va.length_ratio("x" * 125, "y" * 100)))
        self.assertFalse(va.ratio_ok(va.length_ratio("x" * 79, "y" * 100)))
        self.assertFalse(va.ratio_ok(va.length_ratio("x" * 126, "y" * 100)))

    def test_hedge_rate(self):
        self.assertEqual(va.hedge_rate("This is plain."), 0.0)
        self.assertGreater(va.hedge_rate("However, it might depend on the case."), 0)

    def test_validate_file_flags_bad_pairs(self):
        def row(rid, role, body, letter, exp):
            return {"record_id": rid, "role": role, "expected_letter": exp, "body": body,
                    "text": f"{body}\nANSWER: ({letter})", "finish_reason": "stop"}
        good = [row("r1", "aligned", BODY, "A", "A"), row("r1", "opposed", BODY, "B", "B")]
        bad_letter = [row("r2", "aligned", BODY, "B", "A"), row("r2", "opposed", BODY, "B", "B")]
        bad_ratio = [row("r3", "aligned", BODY * 3, "A", "A"), row("r3", "opposed", BODY, "B", "B")]
        rep = va.validate_file(good + bad_letter + bad_ratio)
        self.assertEqual(rep["records"], 3)
        self.assertEqual(rep["records_failing"], 2)
        self.assertEqual(rep["problems"], {"length_ratio": 1, "letter_mismatch": 1})


if __name__ == "__main__":
    unittest.main()
