"""HubSpot API Service

Features:
- Authentication using HubSpot access (OAuth/Private App) tokens
- get_deals() with cursor-based pagination and the requested signature
- Sliding-window rate limiter (150 req / 10 seconds, process-local)
- Robust retries with exponential backoff and 429 Retry-After honoring
- Error handling for common HubSpot API responses
- Credential validation helper
- Structured logging

Example:
    from services.hubspot_api_service import HubSpotAPIService

    svc = HubSpotAPIService(access_token="<TOKEN>")
    ok = svc.validate_credentials()

    data = svc.get_deals(
        access_token="<OPTIONAL_OVERRIDE>",
        limit=100,
        after=None,
        url="/crm/v3/objects/deals",   # optional; relative path or absolute URL
    )
    print(len(data.get("results", [])))

Notes:
- If you run many processes, consider a distributed rate limiter instead of the
  in-process sliding window implemented here.
"""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import json

# ----------------------------- Logging ---------------------------------- #
LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _handler.setFormatter(_formatter)
    LOGGER.addHandler(_handler)
    LOGGER.setLevel(logging.INFO)


# ----------------------------- Errors ----------------------------------- #
class HubSpotAPIError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, request_id: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.request_id = request_id

    def __str__(self) -> str:  # pragma: no cover
        rid = f" (request_id={self.request_id})" if self.request_id else ""
        code = f"[HTTP {self.status}] " if self.status else ""
        return f"{code}{super().__str__()}{rid}"


class UnauthorizedError(HubSpotAPIError):
    pass


class ForbiddenError(HubSpotAPIError):
    pass


class NotFoundError(HubSpotAPIError):
    pass


class RateLimitError(HubSpotAPIError):
    def __init__(self, message: str, retry_after: Optional[float] = None, **kwargs: Any):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(HubSpotAPIError):
    pass


# ----------------------------- Rate Limiter ------------------------------ #
@dataclass
class RateLimitConfig:
    max_requests: int = 150
    window_seconds: float = 10.0


class SlidingWindowRateLimiter:
    """Simple process-local sliding window limiter."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._hits: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        window_start = now - self.config.window_seconds
        while self._hits and self._hits[0] < window_start:
            self._hits.popleft()
        if len(self._hits) >= self.config.max_requests:
            sleep_for = self._hits[0] + self.config.window_seconds - now
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._hits.append(time.monotonic())


# ----------------------------- Service ---------------------------------- #
class HubSpotAPIService:
    """Convenience client for HubSpot CRM v3 with rate limiting and retries."""

    def __init__(
        self,
        access_token: str = "",
        *,
        base_url: str = "https://api.hubapi.com",
        user_agent: str = "hubspot-api-service/1.0",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_initial: float = 0.8,
        backoff_max: float = 8.0,
        rate_limit: Tuple[int, float] = (150, 10.0),
        default_max_pages: int = 50,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        # if not access_token:
        #     raise ValueError("access_token must be provided")
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_initial = backoff_initial
        self.backoff_max = backoff_max
        self.default_max_pages = default_max_pages
        self.session = session or requests.Session()
        self.logger = logger or LOGGER
        self.user_agent = user_agent
        self.rate_limiter = SlidingWindowRateLimiter(
            RateLimitConfig(max_requests=int(rate_limit[0]), window_seconds=float(rate_limit[1]))
        )

    # ------------------------- Internal helpers ------------------------- #
    def _headers(self, override_token: Optional[str] = None) -> Dict[str, str]:
        token = override_token or self.access_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        access_token: Optional[str] = None,
    ) -> requests.Response:
        """Low-level HTTP with retries, backoff, and error handling.
        Returns the raw Response; caller can parse .json().
        """
        # Compose full URL
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.base_url}{path_or_url}"

        attempt = 0
        while True:
            attempt += 1
            self.rate_limiter.acquire()

            try:
                self.logger.debug("HTTP %s %s | params=%s json=%s", method, url, params, json)
                resp = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=self._headers(override_token=access_token),
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                self.logger.warning("Request error on attempt %s: %s", attempt, exc)
                if attempt > self.max_retries:
                    raise HubSpotAPIError(f"Network error after {self.max_retries} retries: {exc}")
                self._sleep_with_backoff(attempt)
                continue

            # Success
            if 200 <= resp.status_code < 300:
                return resp

            request_id = resp.headers.get("X-Request-ID")

            # Specific error handling
            if resp.status_code == 401:
                self._raise_with_payload(UnauthorizedError, resp, request_id)
            elif resp.status_code == 403:
                self._raise_with_payload(ForbiddenError, resp, request_id)
            elif resp.status_code == 404:
                self._raise_with_payload(NotFoundError, resp, request_id)
            elif resp.status_code == 429:
                retry_after = self._parse_retry_after(resp)
                self.logger.warning("Rate limited (429). Retry-After=%.2fs; attempt=%d", retry_after or -1, attempt)
                if attempt > self.max_retries:
                    self._raise_with_payload(RateLimitError, resp, request_id, retry_after=retry_after)
                if retry_after and retry_after > 0:
                    time.sleep(retry_after)
                else:
                    self._sleep_with_backoff(attempt)
                continue
            elif 500 <= resp.status_code < 600:
                self.logger.warning("Server error %d on attempt %d", resp.status_code, attempt)
                if attempt > self.max_retries:
                    self._raise_with_payload(ServerError, resp, request_id)
                self._sleep_with_backoff(attempt)
                continue
            else:
                self._raise_with_payload(HubSpotAPIError, resp, request_id)

    def _sleep_with_backoff(self, attempt: int) -> None:
        delay = min(self.backoff_max, self.backoff_initial * (2 ** (attempt - 1)))
        time.sleep(delay + (0.05 * (attempt % 3)))  # small jitter to avoid thundering herd

    @staticmethod
    def _parse_retry_after(resp: requests.Response) -> Optional[float]:
        val = resp.headers.get("Retry-After")
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    def _raise_with_payload(
        self,
        exc_type: type[HubSpotAPIError],
        resp: requests.Response,
        request_id: Optional[str],
        **kwargs: Any,
    ) -> None:
        try:
            payload = resp.json()
            message = payload.get("message") or payload.get("error") or resp.text
        except ValueError:
            message = resp.text
        raise exc_type(message=message, status=resp.status_code, request_id=request_id, **kwargs)

    # ------------------------- Public methods ---------------------------- #
    def validate_credentials(self) -> bool:
        """Lightweight token check by fetching a minimal page of deals."""
        try:
            resp = self._request("GET", "/crm/v3/objects/deals", params={"limit": 1})
            _ = resp.json()  # ensure JSON parse works
            self.logger.info("Credential validation: success")
            return True
        except UnauthorizedError as e:
            self.logger.error("Credential validation failed: %s", e)
            return False

    def get_deals(
        self,
        *,
        access_token: Optional[str] = None,
        limit: int = 1,
        after: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch HubSpot deals with cursor-based pagination.

        Signature matches the requested style + extra url param:
            api_service.get_data(access_token=..., limit=1, after=..., url=...)

        Args:
            access_token: Optional token override for this call only.
            limit: Page size (HubSpot allows up to 100). If >100, will be clamped to 100.
            after: Cursor to start from (from previous paging.next.after).
            url: Relative path (e.g., "/crm/v3/objects/deals") or absolute URL.

        Returns:
            dict with keys:
              - results: List[dict] of aggregated deals
              - paging: {"next": {"after": str}} when more pages exist, else missing
              - meta: {"pages_fetched": int, "page_size": int}
        """
        if not url:
            url = "/crm/v3/objects/deals"

        # Clamp to API maximum
        if limit < 1:
            limit = 1
        if limit > 100:
            limit = 100

        results: List[Dict[str, Any]] = []
        pages_fetched = 0
        cursor = after

        params = {"limit": limit, "archived": "false"}
        if cursor:
            params["after"] = cursor

        resp = self._request("GET", f"{self.base_url}{url}", params=params, access_token=access_token)
        payload = resp.json() if resp.content else {}

        return payload
        
        '''
        while pages_fetched < self.default_max_pages:
            params = {"limit": limit, "archived": "false"}
            if cursor:
                params["after"] = cursor

            resp = self._request("GET", url, params=params, access_token=access_token)
            payload = resp.json() if resp.content else {}

            page_results = payload.get("results", []) or []
            results.extend(page_results)
            pages_fetched += 1

            # Move the cursor forward
            paging = payload.get("paging") or {}
            next_link = paging.get("next") or {}
            cursor = next_link.get("after")

            self.logger.info(
                "Fetched page %d (%d items)", pages_fetched, len(page_results)
            )

            if not cursor:
                break

        out: Dict[str, Any] = {
            "results": results,
            "meta": {"pages_fetched": pages_fetched, "page_size": limit},
        }
        if cursor:
            out["paging"] = {"next": {"after": cursor}}
        return out
        '''

    # Optional: compatibility adapter if some callers still use `get_data`
    def get_data(
        self,
        *,
        access_token: Optional[str] = None,
        limit: int = 1,
        after: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Alias to get_deals() for backward-compatible signature."""
        return self.get_deals(access_token=access_token, limit=limit, after=after, url=url)


# ----------------------------- CLI Smoke Test --------------------------- #
if __name__ == "__main__":
    import os
    import argparse

    parser = argparse.ArgumentParser(description="HubSpot deals fetcher (smoke test)")
    parser.add_argument("--token", dest="token", default=os.getenv("HUBSPOT_TOKEN"), help="HubSpot access token")
    parser.add_argument("--limit", type=int, default=100, help="Page size (1-100)")
    parser.add_argument("--maxpages", type=int, default=5, help="Max pages to fetch (override default_max_pages)")
    parser.add_argument("--url", default="/crm/v3/objects/deals", help="Relative path or absolute URL")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Provide --token or set HUBSPOT_TOKEN env var")

    # svc = HubSpotAPIService(access_token=args.token, default_max_pages=args.maxpages)
    svc = HubSpotAPIService(base_url="https://api.hubapi.com")
    
    data = svc.get_deals(
        access_token=args.token,
        limit=args.limit,
        # limit=3,
        after=None,
        url="/crm/v3/objects/deals")
    LOGGER.setLevel(logging.DEBUG)

    # print("Valid credentials:", svc.validate_credentials())
    # data = svc.get_deals(limit=args.limit, url=args.url)
    # print(f"Fetched {len(data.get('results', []))} deal(s) across {data.get('meta', {}).get('pages_fetched')} page(s)")

    # for d in data["results"]:
    #     print(d)
    
    print()
    # print(data)
    print()
    print(json.dumps(data, indent=4))