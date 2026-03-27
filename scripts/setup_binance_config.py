#!/usr/bin/env python3
"""
Persist Binance API settings into a local project env file.
"""

from getpass import getpass
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / ".binance.env"


def prompt(label: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    text = f"{label}{suffix}: "
    value = getpass(text) if secret else input(text)
    value = value.strip()
    if not value and default is not None:
        return default
    return value


def main() -> int:
    print("Configure Binance local credentials")
    print(f"Config file: {CONFIG_PATH}")

    mode = prompt("BINANCE_MODE", default="live").lower()
    api_key = prompt("BINANCE_API_KEY")
    api_secret = prompt("BINANCE_API_SECRET", secret=True)
    if mode not in {"live", "testnet"}:
        print("ERROR: BINANCE_MODE must be 'live' or 'testnet'.")
        return 1
    default_base_url = "https://demo-fapi.binance.com" if mode == "testnet" else "https://fapi.binance.com"
    base_url = prompt("BINANCE_FUTURES_BASE_URL", default=default_base_url)
    recv_window = prompt("BINANCE_RECV_WINDOW", default="5000")

    if not api_key or not api_secret:
        print("ERROR: BINANCE_API_KEY and BINANCE_API_SECRET are required.")
        return 1

    content = "\n".join(
        [
            "# Local Binance configuration for no-fomo",
            f"BINANCE_MODE={mode}",
            f"BINANCE_API_KEY={api_key}",
            f"BINANCE_API_SECRET={api_secret}",
            f"BINANCE_FUTURES_BASE_URL={base_url}",
            f"BINANCE_RECV_WINDOW={recv_window}",
            "",
        ]
    )

    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        handle.write(content)

    print("Saved local Binance configuration.")
    print("Future runs will load this file automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
