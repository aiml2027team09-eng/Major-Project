"""Live network packet capture and hybrid IDS inference."""


def run_live_monitor(*args, **kwargs):
    from live_ids.main import run_live_monitor as _run

    return _run(*args, **kwargs)


__all__ = ["run_live_monitor"]
