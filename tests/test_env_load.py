import logging
import tempfile
import unittest
from pathlib import Path

import fixtures  # noqa: F401  (设置 sys.path)
import env_load


class EnvLoadTest(unittest.TestCase):
    def test_parse(self):
        env = env_load.parse_env_text("# c\nA=1\nexport B = \"two\"\nC='x y'\n\nbad line\n")
        self.assertEqual(env, {"A": "1", "B": "two", "C": "x y"})

    def test_missing_or_empty_key_exits_2(self):
        for env in ({}, {env_load.KEY_NAME: ""}):
            with self.assertRaises(SystemExit) as cm:
                env_load.require_key(env)
            self.assertEqual(cm.exception.code, 2)

    def test_does_not_read_inherited_environment(self):
        import os
        os.environ[env_load.KEY_NAME] = "from-inherited-env"
        try:
            with self.assertRaises(SystemExit):
                env_load.require_key({})
        finally:
            del os.environ[env_load.KEY_NAME]

    def test_missing_file_exits(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(SystemExit):
            env_load.load_env(Path(d) / "nope.env")

    def test_assert_no_secret(self):
        env_load.assert_no_secret("nothing here", ["abc123"])
        with self.assertRaises(SystemExit):
            env_load.assert_no_secret("has abc123 inside", ["abc123"])
        with self.assertRaises(SystemExit):
            env_load.assert_no_secret("sk-" + "Z" * 25, [])

    def test_log_redaction(self):
        flt = env_load.RedactFilter(["topsecretvalue"])
        rec = logging.LogRecord("x", logging.INFO, __file__, 1, "key=%s ok sk-%s", ("topsecretvalue", "Q" * 24), None)
        flt.filter(rec)
        self.assertNotIn("topsecretvalue", rec.getMessage())
        self.assertNotIn("QQQQ", rec.getMessage())
        self.assertIn("[REDACTED]", rec.getMessage())


if __name__ == "__main__":
    unittest.main()
