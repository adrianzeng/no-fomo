#!/usr/bin/env python3
"""
Minimal Binance Futures REST client using only the Python standard library.
"""

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).parent.parent
LOCAL_ENV_FILES = [
    BASE_DIR / ".binance.env",
    BASE_DIR / ".env",
]
MODE_BASE_URLS = {
    "live": "https://fapi.binance.com",
    "testnet": "https://demo-fapi.binance.com",
}


class BinanceClientError(RuntimeError):
    """Raised when Binance API access fails."""


def load_local_env() -> None:
    """Load simple KEY=VALUE pairs from local env files if process env is missing."""
    for path in LOCAL_ENV_FILES:
        if not path.exists():
            continue

        with open(path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key and key not in os.environ:
                    os.environ[key] = value


class BinanceFuturesClient:
    """Signed REST client for Binance USDT-M futures endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        mode: str | None = None,
        base_url: str | None = None,
        recv_window: int | None = None,
    ) -> None:
        load_local_env()
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.mode = (mode or os.getenv("BINANCE_MODE") or "live").strip().lower()
        if self.mode not in MODE_BASE_URLS:
            raise BinanceClientError("Invalid BINANCE_MODE. Use 'live' or 'testnet'.")
        resolved_base_url = base_url or os.getenv("BINANCE_FUTURES_BASE_URL") or MODE_BASE_URLS[self.mode]
        self.base_url = resolved_base_url.rstrip("/")
        self.recv_window = recv_window or int(os.getenv("BINANCE_RECV_WINDOW", "5000"))

        if not self.api_key or not self.api_secret:
            raise BinanceClientError(
                "Missing Binance credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET."
            )

    def _sign(self, params: dict[str, Any]) -> str:
        query = urlencode(params, doseq=True)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None, signed: bool = False) -> Any:
        params = dict(params or {})

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self.recv_window
            params["signature"] = self._sign(params)

        query = urlencode(params, doseq=True)
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"

        request = Request(url=url, method=method.upper())
        request.add_header("X-MBX-APIKEY", self.api_key)

        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BinanceClientError(f"Binance API HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise BinanceClientError(f"Binance API connection failed: {exc}") from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise BinanceClientError(f"Binance API returned invalid JSON: {payload[:200]}") from exc

    def get_income_history(
        self,
        start_time: int | None = None,
        end_time: int | None = None,
        symbol: str | None = None,
        income_type: str = "REALIZED_PNL",
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"incomeType": income_type, "limit": min(limit, 1000)}
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/fapi/v1/income", params=params, signed=True)

    def get_user_trades(
        self,
        symbol: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"symbol": symbol.upper(), "limit": min(limit, 1000)}
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        return self._request("GET", "/fapi/v1/userTrades", params=params, signed=True)
