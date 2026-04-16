#!/usr/bin/env python3
"""
Persist Binance API settings into a local project env file.
"""

import argparse
import json
import sys
from getpass import getpass
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / ".binance.env"


def build_json_response(report_type, data=None, error=None):
    response = {
        "meta": {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "status": "error" if error else "ok",
        }
    }
    if error:
        response["error"] = error
    else:
        response["data"] = data
    return response


def prompt(label: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    text = f"{label}{suffix}: "
    value = getpass(text) if secret else input(text)
    value = value.strip()
    if not value and default is not None:
        return default
    return value


def is_interactive() -> bool:
    return bool(sys.stdin and sys.stdin.isatty())


def write_config(mode: str, api_key: str, api_secret: str, base_url: str, recv_window: str) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure local Binance credentials for no-fomo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_binance_config.py
  python setup_binance_config.py --mode testnet --api-key xxx --api-secret yyy
  python setup_binance_config.py --json
        """,
    )
    parser.add_argument("--mode", choices=["live", "testnet"], help="Binance environment mode")
    parser.add_argument("--api-key", help="Binance API key")
    parser.add_argument("--api-secret", help="Binance API secret")
    parser.add_argument("--base-url", help="Override Binance Futures base URL")
    parser.add_argument("--recv-window", default="5000", help="Binance recvWindow in milliseconds")
    parser.add_argument("--json", action="store_true", help="Output machine-readable result")
    args = parser.parse_args()

    interactive = is_interactive()
    has_cli_values = any([args.mode, args.api_key, args.api_secret, args.base_url])

    if not interactive and not has_cli_values:
        error = {
            "code": "non_interactive_missing_args",
            "message": "Non-interactive mode requires --mode, --api-key, and --api-secret.",
        }
        if args.json:
            print(json.dumps(build_json_response("binance_config", error=error), indent=2, ensure_ascii=False))
        else:
            print(f"ERROR: {error['message']}")
        return 1

    if interactive:
        print("Configure Binance local credentials")
        print(f"Config file: {CONFIG_PATH}")

    mode = args.mode or (prompt("BINANCE_MODE", default="live").lower() if interactive else "live")
    if mode not in {"live", "testnet"}:
        error = {"code": "invalid_mode", "message": "BINANCE_MODE must be 'live' or 'testnet'."}
        if args.json:
            print(json.dumps(build_json_response("binance_config", error=error), indent=2, ensure_ascii=False))
        else:
            print(f"ERROR: {error['message']}")
        return 1

    default_base_url = "https://demo-fapi.binance.com" if mode == "testnet" else "https://fapi.binance.com"
    api_key = args.api_key or (prompt("BINANCE_API_KEY") if interactive else "")
    api_secret = args.api_secret or (prompt("BINANCE_API_SECRET", secret=True) if interactive else "")
    base_url = args.base_url or (prompt("BINANCE_FUTURES_BASE_URL", default=default_base_url) if interactive else default_base_url)
    recv_window = args.recv_window if args.recv_window else "5000"

    if not api_key or not api_secret:
        error = {"code": "missing_credentials", "message": "BINANCE_API_KEY and BINANCE_API_SECRET are required."}
        if args.json:
            print(json.dumps(build_json_response("binance_config", error=error), indent=2, ensure_ascii=False))
        else:
            print(f"ERROR: {error['message']}")
        return 1

    write_config(mode, api_key, api_secret, base_url, recv_window)

    result = {
        "config_path": str(CONFIG_PATH),
        "mode": mode,
        "base_url": base_url,
        "recv_window": recv_window,
        "saved": True,
    }
    if args.json:
        print(json.dumps(build_json_response("binance_config", data=result), indent=2, ensure_ascii=False))
    else:
        print("Saved local Binance configuration.")
        print("Future runs will load this file automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
