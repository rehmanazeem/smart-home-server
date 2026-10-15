"""Pure helpers for the YAML-backed relay state and log tailing."""
import os


def relay_key(relay_num: int) -> str:
    """Config key for a relay, e.g. 1 -> 'relay_1'."""
    return f"relay_{relay_num}"


def default_config() -> dict:
    """Factory defaults written by POST /reset."""
    return {
        "esp": {"connect": False, "ip": "192.168.1.50", "port": 8080},
        "relay_1": {"state": False},
        "relay_2": {"state": False},
    }


def toggle_state(config: dict, relay_num: int) -> dict:
    """Flip a relay's state in `config` in place and return that relay's entry."""
    entry = config[relay_key(relay_num)]
    entry["state"] = not entry["state"]
    return entry


def tail_latest_log(log_dir: str, n: int = 20) -> list[str]:
    """Last `n` lines of the newest `log_*` file in `log_dir` (names sort by date)."""
    files = sorted(f for f in os.listdir(log_dir) if f.startswith("log_"))
    if not files:
        return []
    with open(os.path.join(log_dir, files[-1]), "r") as f:
        return f.readlines()[-n:]
