"""Safety guard for superseded pipelines that bypass the shared literal gate."""


def retired_legacy_pipeline(name: str) -> None:
    """Stop obsolete entrypoints, without altering or rerunning their evidence.

    These historical drivers exempted a registry control, generated claims
    from unverified scores, or wrote a stale site. They are kept as research
    history only. A replacement must use the shared tools and satisfy the
    currently assigned protocol; there is deliberately no environment override.
    """
    raise SystemExit(
        f"{name} is retired: it can bypass the literal all-registry stop or "
        "publish unverified claims. See evidence/focus_reaudit_20261027.json "
        "and use the shared gate; no experiment or slot was started."
    )
