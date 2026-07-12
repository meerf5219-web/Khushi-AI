import html
import logging
import re
import time
from typing import Any, List, Optional
from urllib.parse import quote_plus

import requests

try:
    from duckduckgo_search import DDGS  # type: ignore
    _DDGS_BACKEND = "duckduckgo_search"
except ModuleNotFoundError:
    try:
        from ddgs import DDGS  # type: ignore
        _DDGS_BACKEND = "ddgs"
    except ModuleNotFoundError:
        DDGS = None  # type: ignore
        _DDGS_BACKEND = "html_fallback"

logger = logging.getLogger(__name__)


class SearchWebSkill:
    """
    DuckDuckGo web search skill.

    Requirements:
    - search(query)
    - summarize(results)
    - execute(text)
    """

    def __init__(self) -> None:
        self._ddgs = DDGS() if DDGS is not None else None
        if _DDGS_BACKEND == "html_fallback":
            logger.info("[SEARCH BACKEND] Using DuckDuckGo HTML fallback (duckduckgo_search not installed).")
        else:
            logger.info("[SEARCH BACKEND] Using DDGS via '%s'.", _DDGS_BACKEND)

    def execute(self, text: str) -> Optional[str]:
        normalized_text = (text or "").strip()
        if not normalized_text:
            return None

        # Try to extract an actual query from the utterance.
        # Examples:
        # - "latest AI news"
        # - "Who won yesterday's IPL match?"
        # - "Search Python programming"
        query = self._extract_query(normalized_text)
        if not query:
            query = normalized_text

        logger.info("Detected WEB_SEARCH")
        logger.info("Search query: %s", query)

        if self._ddgs is None:
            logger.info("[SEARCH BACKEND] HTML fallback active — DDGS unavailable.")
        start = time.perf_counter()
        results = self.search(query)
        elapsed = time.perf_counter() - start
        logger.info("Search time: %.3fs", elapsed)

        return self.summarize(results)

    def search(self, query: str) -> List[dict[str, Any]]:
        """
        Perform DuckDuckGo search and return raw results.

        Returns up to ~5 results (we'll pick top 3 for speaking).
        """
        if self._ddgs is not None:
            # Using DDGS.text for lightweight search results.
            # Each item is typically: {'title': ..., 'href': ..., 'body'/'snippet': ...}
            results: List[dict[str, Any]] = []
            try:
                for item in self._ddgs.text(query, max_results=5):
                    results.append(dict(item))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("DDGS search failed: %s", exc)
            return results

        # Fallback: scrape DuckDuckGo HTML results (no external deps).
        # This keeps web search functional even when `ddgs` isn't installed.
        return self._scrape_duckduckgo_html(query)

    def summarize(self, results: List[dict[str, Any]]) -> str:
        """
        Summarize top 3 results into a concise spoken format.
        """
        if not results:
            return "I couldn't find anything relevant online."

        top = results[:3]

        parts: List[str] = []
        for i, item in enumerate(top, start=1):
            title = (item.get("title") or "").strip()
            url = (item.get("href") or item.get("url") or "").strip()
            snippet = (item.get("snippet") or item.get("body") or item.get("description") or "").strip()

            snippet = self._truncate(snippet, 170)

            if title and snippet:
                parts.append(f"{i}. {title}. {snippet}")
            elif title:
                parts.append(f"{i}. {title}.")
            else:
                parts.append(f"{i}. {snippet or 'No snippet available.'}")

            # URL is usually not spoken, but keep behavior resilient (no-op).
            _ = url

        # 3 items in one answer; 2-4 sentences-ish.
        return " ".join(parts)

    def _extract_query(self, text: str) -> Optional[str]:
        lowered = text.lower().strip()

        # Remove leading trigger words/phrases if present.
        lowered = re.sub(r"^(latest|today|current|news|search|find)\s+", "", lowered)
        # Handle "search <query>" style
        lowered = re.sub(r"^search\s+", "", lowered)

        # Keep "weather in delhi" etc as-is for web search.
        query = lowered.strip(" ?!.,")

        return query or None

    def _scrape_duckduckgo_html(self, query: str) -> List[dict[str, Any]]:
        results: List[dict[str, Any]] = []
        try:
            url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; KhushiAI/1.0)"}
            resp = requests.get(url, headers=headers, timeout=12)
            resp.raise_for_status()

            # Very lightweight parsing:
            # - Result titles appear in <a rel="nofollow" class="result__a" ...>Title</a>
            # - Snippet appears in <a ...>Title</a> ... <a ...>snippet text</a> OR in nearby elements.
            # We use regex to extract top blocks.
            text = resp.text

            # Extract candidate blocks around result anchors.
            anchors = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            # Extract snippets from result blocks (best-effort).
            snippets = re.findall(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            def clean(s: str) -> str:
                s = html.unescape(s)
                s = re.sub(r"<.*?>", " ", s)
                s = re.sub(r"\s+", " ", s).strip()
                return s

            for i, (href, title_html) in enumerate(anchors[:5]):
                title = clean(title_html)
                snippet = ""
                if i < len(snippets):
                    snippet = clean(snippets[i])

                if not title and not snippet:
                    continue

                results.append(
                    {
                        "title": title,
                        "href": href,
                        "body": snippet or "",
                    }
                )
                if len(results) >= 5:
                    break
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("DuckDuckGo HTML scrape failed: %s", exc)

        return results

    def _truncate(self, s: str, max_len: int) -> str:
        s = re.sub(r"\s+", " ", s).strip()
        if len(s) <= max_len:
            return s
        return s[: max_len - 1].rstrip() + "…"
