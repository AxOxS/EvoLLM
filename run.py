#!/usr/bin/env python3
"""EvoLLM Frontend Launcher."""

import subprocess
import sys


def main():
    subprocess.run(
        [sys.executable, "-m", "frontend.main"],
        cwd=sys.path[0] or ".",
    )


if __name__ == "__main__":
    main()
