#!/usr/bin/env python3
"""Build all generated assets — run after changing identities or templates."""
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
STEPS = [
    "generate_identities_js.py",
    "generate_template.py",
    "verify_assets.py",
]


def main():
    for step in STEPS:
        script = SCRIPTS / step
        print(f"\n==> {step}")
        result = subprocess.run([sys.executable, str(script)], cwd=SCRIPTS.parent)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    print("\nBuild complete.")


if __name__ == "__main__":
    main()