"""Build the LeadDock wheel with a frozen archive timestamp."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SOURCE_DATE_EPOCH = "1786558244"
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(args.outdir.resolve()),
        ],
        cwd=ROOT,
        env=env,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
