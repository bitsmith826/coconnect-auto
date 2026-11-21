import time
import json
from typing import Optional, Dict, Any

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CURL_CFFI = False

class CoConnectClient:
    def __init__(self, proxy: Optional[str] = None, max_retries: int = 3):
        if proxy and not (proxy.startswith("http://") or proxy.startswith("https://") or proxy.startswith("socks5://")):
            proxy = f"http://{proxy}"
        self.proxy = proxy
        self.max_retries = max_retries
        
        if HAS_CURL_CFFI:
            self.session = cffi_requests.Session(impersonate="chrome120")
        else:
            self.session = cffi_requests.Session()
            
        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
            
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://hub.coconnect.co/auth",
            "Origin": "https://hub.coconnect.co",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })

    def _request_with_retry(self, method: str, url: str, **kwargs) -> Any:
        kwargs.setdefault("timeout", 20)
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = getattr(self.session, method.lower())(url, **kwargs)
                # Jika server mengembalikan 429 Too Many Requests atau 502/503/504 Bad Gateway, lakukan backoff retry
                if resp.status_code in [429, 502, 503, 504]:
                    if attempt < self.max_retries:
                        retry_after = resp.headers.get("Retry-After")
                        sleep_time = float(retry_after) if retry_after and retry_after.isdigit() else (2.0 * attempt)
                        time.sleep(sleep_time)
                        continue
                return resp
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    time.sleep(1.5 * attempt)
                else:
                    raise last_exception

    def get(self, url: str, **kwargs) -> Any:
        return self._request_with_retry("get", url, **kwargs)

    def post(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        return self._request_with_retry("post", url, json=json, **kwargs)

    def patch(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        return self._request_with_retry("patch", url, json=json, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        return self._request_with_retry("delete", url, **kwargs)

    def close(self):
        """Menutup session client untuk mencegah memory/socket leak."""
        try:
            self.session.close()
        except Exception:
            pass

    @staticmethod
    def safe_json(resp: Any) -> Dict[str, Any]:
        """Ekstraksi JSON yang aman dari response HTTP."""
        if resp is None:
            return {}
        try:
            return resp.json()
        except Exception:
            return {}
