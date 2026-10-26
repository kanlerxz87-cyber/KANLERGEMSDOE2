#!/usr/bin/env python3
"""Collect unittest and pytest tests, retaining failure status and CI annotations."""
import subprocess
import sys

result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(result.stdout, end="")
if result.returncode:
    message = result.stdout.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print("::error title=Test failure details::" + message)
raise SystemExit(result.returncode)
