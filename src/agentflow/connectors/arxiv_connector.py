# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import re
import socket
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timezone
from http.client import RemoteDisconnected
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from agentflow.connectors.base import BaseConnector
else:
    from .base import BaseConnector


_ARXIV_ID_RE = re.compile(r"^(?P<id>(?:\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)$")
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "opensearch": "http://a9.com/-/spec/opensearch/1.1/"}
_ALLOWED_SORT_BY = {"relevance", "submittedDate", "lastUpdatedDate"}
_ALLOWED_SORT_ORDER = {"ascending", "descending"}
_DEFAULT_TIMEOUT = 60.0
_DEFAULT_RETRIES = 2
_DEFAULT_BACKOFF = 1.0


@dataclass(slots=True)
class ArxivPaper:
    """Normalized arXiv paper reference."""

    arxiv_id: str
    abs_url: str
    pdf_url: str


@dataclass(slots=True)
class ArxivSearchResult:
    """Normalized arXiv search result."""

    arxiv_id: str
    title: str
    summary: str
    authors: tuple[str, ...]
    published: str | None
    updated: str | None
    abs_url: str
    pdf_url: str


@dataclass(slots=True)
class ArxivSearchPage:
    """Normalized arXiv search page with metadata."""

    results: tuple[ArxivSearchResult, ...]
    total_results: int
    start_index: int
    items_per_page: int
    search_query: str
    sort_by: str
    sort_order: str


class ArxivConnectorError(RuntimeError):
    """Raised when arXiv normalization or download fails."""


class ArxivQueryError(ArxivConnectorError):
    """Raised when the caller passes an invalid arXiv query."""


class ArxivParseError(ArxivConnectorError):
    """Raised when arXiv returns malformed or incomplete XML."""


class ArxivNetworkError(ArxivConnectorError):
    """Raised when a network request to arXiv fails."""


class ArxivTimeoutError(ArxivNetworkError):
    """Raised when a request to arXiv times out."""


class ArxivRateLimitError(ArxivNetworkError):
    """Raised when arXiv rate limits the client."""


class ArxivConnector(BaseConnector):
    """Fetch and search arXiv papers."""

    def __init__(
        self,
        *,
        timeout: float = _DEFAULT_TIMEOUT,
        user_agent: str | None = None,
        max_retries: int = _DEFAULT_RETRIES,
        backoff_factor: float = _DEFAULT_BACKOFF,
    ) -> None:
        self.timeout = timeout
        self.user_agent = user_agent or "AGENTFlow/0.1.0 (arxiv-connector)"
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def resolve(self, value: str) -> ArxivPaper:
        arxiv_id = self._normalize_arxiv_id(value)
        return ArxivPaper(
            arxiv_id=arxiv_id,
            abs_url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        )

    def get_pdf_url(self, value: str) -> str:
        return self.resolve(value).pdf_url

    def search(
        self,
        query: str | None = None,
        *,
        search_query: str | None = None,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
        abstract: str | None = None,
        max_results: int = 10,
        start: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        date_from: str | date | datetime | None = None,
        date_to: str | date | datetime | None = None,
        return_page: bool = False,
    ) -> list[ArxivSearchResult] | ArxivSearchPage:
        page = self.search_page(
            query=query,
            search_query=search_query,
            title=title,
            author=author,
            category=category,
            abstract=abstract,
            max_results=max_results,
            start=start,
            sort_by=sort_by,
            sort_order=sort_order,
            date_from=date_from,
            date_to=date_to,
        )
        if return_page:
            return page
        return list(page.results)

    def search_page(
        self,
        query: str | None = None,
        *,
        search_query: str | None = None,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
        abstract: str | None = None,
        max_results: int = 10,
        start: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        date_from: str | date | datetime | None = None,
        date_to: str | date | datetime | None = None,
    ) -> ArxivSearchPage:
        if max_results <= 0:
            raise ArxivQueryError("max_results must be greater than 0.")
        if start < 0:
            raise ArxivQueryError("start must be >= 0.")
        if sort_by not in _ALLOWED_SORT_BY:
            raise ArxivQueryError(f"Unsupported sort_by: {sort_by}")
        if sort_order not in _ALLOWED_SORT_ORDER:
            raise ArxivQueryError(f"Unsupported sort_order: {sort_order}")

        normalized_query = self._build_search_query(
            query=query,
            search_query=search_query,
            title=title,
            author=author,
            category=category,
            abstract=abstract,
        )
        url = (
            "https://export.arxiv.org/api/query?"
            f"search_query={quote_plus(normalized_query)}"
            f"&start={start}&max_results={max_results}"
            f"&sortBy={sort_by}&sortOrder={sort_order}"
        )
        xml_text = self._request_text(url)
        page = self._parse_search_feed(
            xml_text,
            search_query=normalized_query,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        if date_from is None and date_to is None:
            return page
        filtered_results = tuple(
            item
            for item in page.results
            if self._matches_date_range(item, date_from=date_from, date_to=date_to)
        )
        return ArxivSearchPage(
            results=filtered_results,
            total_results=len(filtered_results),
            start_index=page.start_index,
            items_per_page=len(filtered_results),
            search_query=page.search_query,
            sort_by=page.sort_by,
            sort_order=page.sort_order,
        )

    def download_pdf(
        self,
        value: str,
        *,
        output_path: str | Path | None = None,
        overwrite: bool = False,
    ) -> Path:
        paper = self.resolve(value)
        target = (
            Path(output_path).expanduser().resolve()
            if output_path is not None
            else Path.cwd() / f"{paper.arxiv_id.replace('/', '_')}.pdf"
        )
        if target.exists() and not overwrite:
            raise ArxivConnectorError(
                f"Target file already exists: {target}. Set overwrite=True to replace it."
            )
        target.parent.mkdir(parents=True, exist_ok=True)

        content, content_type = self._request_bytes(paper.pdf_url)
        if "pdf" not in content_type.lower() and not content.startswith(b"%PDF"):
            raise ArxivConnectorError(
                f"Expected a PDF response from arXiv, got content-type={content_type or 'unknown'}."
            )

        target.write_bytes(content)
        return target

    def _request_text(self, url: str) -> str:
        content, _ = self._request_bytes(url)
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ArxivParseError("Failed to decode arXiv response as UTF-8.") from exc

    def _request_bytes(self, url: str) -> tuple[bytes, str]:
        request = Request(
            url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    return response.read(), response.headers.get("Content-Type", "")
            except HTTPError as exc:
                if exc.code == 429:
                    last_error = ArxivRateLimitError("arXiv rate limit exceeded.")
                    if attempt < self.max_retries:
                        self._sleep_before_retry(attempt)
                        continue
                    raise last_error from exc
                if 500 <= exc.code < 600 and attempt < self.max_retries:
                    last_error = ArxivNetworkError(f"arXiv server error: HTTP {exc.code}")
                    self._sleep_before_retry(attempt)
                    continue
                raise ArxivNetworkError(f"arXiv request failed with HTTP {exc.code}") from exc
            except (TimeoutError, socket.timeout) as exc:
                last_error = ArxivTimeoutError("arXiv request timed out.")
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise last_error from exc
            except (RemoteDisconnected, URLError, ConnectionError, OSError) as exc:
                last_error = ArxivNetworkError(str(exc))
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise last_error from exc
        if last_error is not None:
            raise last_error
        raise ArxivNetworkError("Unknown arXiv network failure.")

    def _parse_search_feed(
        self,
        xml_text: str,
        *,
        search_query: str,
        sort_by: str,
        sort_order: str,
    ) -> ArxivSearchPage:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ArxivParseError("Failed to parse arXiv Atom response.") from exc

        total_results = self._parse_int(root, "opensearch:totalResults", default=0)
        start_index = self._parse_int(root, "opensearch:startIndex", default=0)
        items_per_page = self._parse_int(root, "opensearch:itemsPerPage", default=0)

        results: list[ArxivSearchResult] = []
        for entry in root.findall("atom:entry", _ATOM_NS):
            entry_id = self._child_text(entry, "atom:id")
            title = self._normalize_whitespace(self._child_text(entry, "atom:title"))
            summary = self._normalize_whitespace(self._child_text(entry, "atom:summary"))
            published = self._child_text(entry, "atom:published", required=False)
            updated = self._child_text(entry, "atom:updated", required=False)
            authors = tuple(
                self._normalize_whitespace(node.text or "")
                for node in entry.findall("atom:author/atom:name", _ATOM_NS)
                if (node.text or "").strip()
            )

            abs_url = entry_id.strip()
            paper = self.resolve(abs_url)
            results.append(
                ArxivSearchResult(
                    arxiv_id=paper.arxiv_id,
                    title=title,
                    summary=summary,
                    authors=authors,
                    published=published.strip() if published else None,
                    updated=updated.strip() if updated else None,
                    abs_url=paper.abs_url,
                    pdf_url=paper.pdf_url,
                )
            )

        return ArxivSearchPage(
            results=tuple(results),
            total_results=total_results,
            start_index=start_index,
            items_per_page=items_per_page or len(results),
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        return " ".join(value.split())

    @staticmethod
    def _child_text(element: ET.Element, path: str, *, required: bool = True) -> str | None:
        node = element.find(path, _ATOM_NS)
        if node is not None and node.text is not None:
            return node.text
        if required:
            raise ArxivParseError(f"Missing expected arXiv feed field: {path}")
        return None

    @staticmethod
    def _parse_int(element: ET.Element, path: str, *, default: int = 0) -> int:
        node = element.find(path, _ATOM_NS)
        if node is None or node.text is None:
            return default
        try:
            return int(node.text.strip())
        except ValueError:
            return default

    @classmethod
    def _normalize_arxiv_id(cls, value: str) -> str:
        raw = value.strip()
        if not raw:
            raise ArxivConnectorError("arXiv id or URL cannot be empty.")

        parsed = urlparse(raw)
        candidate = raw
        if parsed.scheme and parsed.netloc:
            if "arxiv.org" not in parsed.netloc.lower():
                raise ArxivConnectorError(f"Unsupported host for arXiv connector: {parsed.netloc}")
            path = parsed.path.strip("/")
            parts = [part for part in path.split("/") if part]
            if len(parts) < 2 or parts[0] not in {"abs", "pdf"}:
                raise ArxivConnectorError(f"Unsupported arXiv URL format: {raw}")
            candidate = parts[1]
            if parts[0] == "pdf" and candidate.endswith(".pdf"):
                candidate = candidate[:-4]

        match = _ARXIV_ID_RE.match(candidate)
        if not match:
            raise ArxivConnectorError(f"Invalid arXiv id or URL: {value}")
        return match.group("id")

    @staticmethod
    def _sleep_before_retry(attempt: int) -> None:
        time.sleep(_DEFAULT_BACKOFF * (2**attempt))

    @classmethod
    def _build_search_query(
        cls,
        *,
        query: str | None,
        search_query: str | None,
        title: str | None,
        author: str | None,
        category: str | None,
        abstract: str | None,
    ) -> str:
        if search_query is not None:
            if any(value for value in (query, title, author, category, abstract)):
                raise ArxivQueryError(
                    "search_query cannot be combined with query/title/author/category/abstract."
                )
            normalized = search_query.strip()
            if not normalized:
                raise ArxivQueryError("search_query cannot be empty.")
            return normalized

        clauses: list[str] = []
        if query:
            clauses.append(f"all:{cls._escape_query_value(query)}")
        if title:
            clauses.append(f"ti:{cls._escape_query_value(title)}")
        if author:
            clauses.append(f"au:{cls._escape_query_value(author)}")
        if category:
            clauses.append(f"cat:{cls._escape_query_value(category)}")
        if abstract:
            clauses.append(f"abs:{cls._escape_query_value(abstract)}")
        if not clauses:
            raise ArxivQueryError("At least one query input is required.")
        return " AND ".join(clauses)

    @staticmethod
    def _escape_query_value(value: str) -> str:
        normalized = " ".join(value.split()).strip()
        if not normalized:
            raise ArxivQueryError("Search fields cannot be empty.")
        if any(char in normalized for char in '"'):
            normalized = normalized.replace('"', '')
        return f'"{normalized}"' if " " in normalized else normalized

    @classmethod
    def _matches_date_range(
        cls,
        result: ArxivSearchResult,
        *,
        date_from: str | date | datetime | None,
        date_to: str | date | datetime | None,
    ) -> bool:
        published = cls._coerce_datetime(result.published)
        if published is None:
            return False
        start = cls._coerce_datetime(date_from)
        end = cls._coerce_datetime(date_to)
        if start is not None and published < start:
            return False
        if end is not None and published > end:
            return False
        return True

    @staticmethod
    def _coerce_datetime(value: str | date | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        raw = value.strip()
        if not raw:
            return None
        try:
            if len(raw) == 10:
                parsed = datetime.fromisoformat(raw)
                return parsed.replace(tzinfo=timezone.utc)
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ArxivQueryError(f"Invalid date value: {value}") from exc


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("value", nargs="?", help="arXiv id, abs URL, or pdf URL")
    parser.add_argument("--output", help="Target PDF path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing target file")
    parser.add_argument("--search", help="Free-text query routed to all:<query>")
    parser.add_argument("--search-query", help="Raw arXiv search_query expression")
    parser.add_argument("--title", help="Title-specific search field")
    parser.add_argument("--author", help="Author-specific search field")
    parser.add_argument("--category", help="Category-specific search field")
    parser.add_argument("--abstract", help="Abstract-specific search field")
    parser.add_argument("--max-results", type=int, default=5, help="Max search results")
    parser.add_argument("--start", type=int, default=0, help="Start offset")
    parser.add_argument("--sort-by", default="relevance", choices=sorted(_ALLOWED_SORT_BY))
    parser.add_argument("--sort-order", default="descending", choices=sorted(_ALLOWED_SORT_ORDER))
    parser.add_argument("--date-from", help="Filter published date from YYYY-MM-DD")
    parser.add_argument("--date-to", help="Filter published date to YYYY-MM-DD")
    parser.add_argument("--timeout", type=float, default=_DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=_DEFAULT_RETRIES, help="Retry count for transient errors")
    args = parser.parse_args()

    connector = ArxivConnector(timeout=args.timeout, max_retries=args.retries)

    if any((args.search, args.search_query, args.title, args.author, args.category, args.abstract)):
        page = connector.search_page(
            query=args.search,
            search_query=args.search_query,
            title=args.title,
            author=args.author,
            category=args.category,
            abstract=args.abstract,
            max_results=args.max_results,
            start=args.start,
            sort_by=args.sort_by,
            sort_order=args.sort_order,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        print("total_results:", page.total_results)
        print("start_index:", page.start_index)
        print("items_per_page:", page.items_per_page)
        print("search_query:", page.search_query)
        for index, item in enumerate(page.results, start=1):
            print(f"[{index}] {item.arxiv_id}")
            print("title:", item.title)
            print("authors:", ", ".join(item.authors))
            print("published:", item.published)
            print("updated:", item.updated)
            print("pdf_url:", item.pdf_url)
            print()
        return

    if not args.value:
        raise SystemExit("Provide an arXiv id/URL, use --search, or use --search-query.")

    paper = connector.resolve(args.value)
    print("arxiv_id:", paper.arxiv_id)
    print("abs_url:", paper.abs_url)
    print("pdf_url:", paper.pdf_url)

    if args.output:
        path = connector.download_pdf(
            args.value,
            output_path=Path(args.output),
            overwrite=args.overwrite,
        )
        print("downloaded_to:", path)


if __name__ == "__main__":
    _main()
