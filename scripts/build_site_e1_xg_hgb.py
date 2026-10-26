"""Compatibility entry point for rebuilding the current evidence-first site.

The historical E1 page generator contained unresolved conflict markers and
published a download link for an artifact that is now quarantined. Use the
main builder, which renders the E1 run card as an explicitly negative,
research-only record with no TIFF or ZIP download.
"""
from build_site import build

if __name__ == '__main__':
    build()
