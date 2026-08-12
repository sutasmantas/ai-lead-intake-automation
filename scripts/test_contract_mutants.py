"""Kill construction-known defects in the public booking/CRM contract."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "leaddock" / "contracts.py"
TEST = ROOT / "tests" / "test_contracts.py"

MUTANTS = {
    "allow-naive-slot": (
        "if slot.tzinfo is None:",
        "if False and slot.tzinfo is None:",
    ),
    "allow-off-boundary-slot": (
        "if slot.minute not in (0, 30) or slot.second or slot.microsecond:",
        "if False:",
    ),
    "remove-replay-lookup": (
        "if key in self.by_idempotency:",
        "if False and key in self.by_idempotency:",
    ),
    "weaken-overlap-check": (
        "if start < existing_end and end > existing_start:",
        "if start < existing_end and end < existing_start:",
    ),
    "change-booking-duration": (
        "end = start + timedelta(minutes=30)",
        "end = start + timedelta(minutes=60)",
    ),
    "show-occupied-slot": (
        "if any(\n                    datetime.fromisoformat(booking.start_utc) == utc",
        "if False and any(\n                    datetime.fromisoformat(booking.start_utc) == utc",
    ),
    "corrupt-crm-identity": (
        '"external_key": lead["identity_key"],',
        '"external_key": lead["id"],',
    ),
    "return-stored-crm-object": ("return deepcopy(record)", "return record"),
}


def run(source: str) -> int:
    with tempfile.TemporaryDirectory(prefix="leaddock-mutant-") as raw:
        temp = Path(raw)
        package = temp / "leaddock"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "contracts.py").write_text(source, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(temp)
        result = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=temp,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode


def main() -> int:
    clean = SOURCE.read_text(encoding="utf-8")
    if run(clean) != 0:
        print("FAIL clean control", file=sys.stderr)
        return 1
    print("PASS clean control")
    missed = []
    for name, (old, new) in MUTANTS.items():
        if clean.count(old) != 1:
            print(f"FAIL {name}: mutation target count is {clean.count(old)}")
            missed.append(name)
            continue
        mutant = clean.replace(old, new, 1)
        if run(mutant) == 0:
            print(f"SURVIVED {name}")
            missed.append(name)
        else:
            print(f"KILLED {name}")
    if missed:
        print(f"FAIL {len(missed)} mutant(s): {', '.join(missed)}", file=sys.stderr)
        return 1
    print(f"PASS {len(MUTANTS)}/{len(MUTANTS)} mutants killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
