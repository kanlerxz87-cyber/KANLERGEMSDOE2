#!/usr/bin/env python3
"""Withdrawn legacy entry point. No experiment or scientific result is produced."""
import sys

def main():
    print("BLOCKED: legacy pipeline withdrawn: incompatible evaluator, incomplete lane/registry/baseline evidence. "
          "See research/pipeline-review.md and vendor/template/pins.json. No TIFF or score produced.", file=sys.stderr)
    return 2

if __name__ == '__main__':
    raise SystemExit(main())
