#!/usr/bin/env python3
"""凭证读取与脱敏（实施计划 §1 第 1 项）。

  * 只从显式给出的 .env 文件读取，不依赖继承的环境变量（设计 H3：继承环境里键不存在）。
  * 键缺失或为空 → SystemExit(2)。
  * 只报告键的「存在性与长度」，从不输出值。
  * 提供日志脱敏过滤器，以及写入工件前的密钥扫描。

只用标准库。
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

KEY_NAME = "DEEPSEEK_API_KEY"
DEFAULT_BASE_URL = "https://api.deepseek.com"
SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def parse_env_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k.strip()] = v
    return out


def load_env(path: str | Path) -> dict[str, str]:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"找不到 .env 文件：{p}（请用 --env-file 指定）")
    return parse_env_text(p.read_text(encoding="utf-8-sig"))


def require_key(env: dict[str, str], name: str = KEY_NAME) -> str:
    value = env.get(name, "")
    if not value:
        print(f"错误：{name} 缺失或为空", file=sys.stderr)
        raise SystemExit(2)
    return value


class RedactFilter(logging.Filter):
    """把日志里出现的密钥值和 sk-… 样式字符串替换掉。"""

    def __init__(self, secrets: list[str]):
        super().__init__()
        self.secrets = [s for s in secrets if s]

    def _scrub(self, text: str) -> str:
        for s in self.secrets:
            text = text.replace(s, "[REDACTED]")
        return SECRET_PATTERN.sub("[REDACTED]", text)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._scrub(record.getMessage())
        record.args = ()
        return True


def install_redaction(secrets: list[str]) -> None:
    flt = RedactFilter(secrets)
    root = logging.getLogger()
    root.addFilter(flt)
    for h in root.handlers:
        h.addFilter(flt)


def assert_no_secret(text: str, secrets: list[str]) -> None:
    """写入任何工件之前调用；命中即中止。"""
    for s in secrets:
        if s and s in text:
            raise SystemExit("中止写入：内容含有密钥值")
    if SECRET_PATTERN.search(text):
        raise SystemExit("中止写入：内容含有 sk-… 样式的字符串")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env-file", default=".env", help="默认当前目录的 .env")
    args = ap.parse_args(argv)
    env = load_env(args.env_file)
    key = require_key(env)
    print(f"{KEY_NAME}: 已设置，长度 {len(key)}")
    print(f"DEEPSEEK_BASE_URL: {env.get('DEEPSEEK_BASE_URL', DEFAULT_BASE_URL)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
