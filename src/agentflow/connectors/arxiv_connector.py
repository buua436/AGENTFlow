from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen


_ARXIV_ID_RE = re.compile(r"^(?P<id>(?:\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)$")
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


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


class ArxivConnectorError(RuntimeError):
    """Raised when arXiv normalization or download fails."""


class ArxivConnector:
    """Fetch and search arXiv papers."""

    def __init__(self, *, timeout: float = 60.0, user_agent: str | None = None) -> None:
        self.timeout = timeout
        self.user_agent = user_agent or "AGENTFlow/0.1.0 (arxiv-connector)"

    def resolve(self, value: str) -> ArxivPaper:
        arxiv_id = self._normalize_arxiv_id(value)
        return ArxivPaper(
            arxiv_id=arxiv_id,
            abs_url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        )

    def get_pdf_url(self, value: str) -> str:
        return self.resolve(value).pdf_url

    def search(self, query: str, *, max_results: int = 10, start: int = 0) -> list[ArxivSearchResult]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ArxivConnectorError("Search query cannot be empty.")
        if max_results <= 0:
            raise ArxivConnectorError("max_results must be greater than 0.")
        if start < 0:
            raise ArxivConnectorError("start must be >= 0.")

        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{quote_plus(normalized_query)}&start={start}&max_results={max_results}"
        )
        xml_text = self._request_text(url)
        return self._parse_search_feed(xml_text)

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

        request = Request(
            paper.pdf_url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                content = response.read()
        except Exception as exc:
            raise ArxivConnectorError(str(exc)) from exc

        if "pdf" not in content_type.lower() and not content.startswith(b"%PDF"):
            raise ArxivConnectorError(
                f"Expected a PDF response from arXiv, got content-type={content_type or 'unknown'}."
            )

        target.write_bytes(content)
        return target

    def _request_text(self, url: str) -> str:
        request = Request(
            url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            raise ArxivConnectorError(str(exc)) from exc

    def _parse_search_feed(self, xml_text: str) -> list[ArxivSearchResult]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ArxivConnectorError("Failed to parse arXiv Atom response.") from exc

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
        return results

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        return " ".join(value.split())

    @staticmethod
    def _child_text(element: ET.Element, path: str, *, required: bool = True) -> str | None:
        node = element.find(path, _ATOM_NS)
        if node is not None and node.text is not None:
            return node.text
        if required:
            raise ArxivConnectorError(f"Missing expected arXiv feed field: {path}")
        return None

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


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("value", nargs="?", help="arXiv id, abs URL, or pdf URL")
    parser.add_argument("--output", help="Target PDF path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing target file")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--max-results", type=int, default=5, help="Max search results")
    args = parser.parse_args()

    connector = ArxivConnector()

    if args.search:
        results = connector.search(args.search, max_results=args.max_results)
        for index, item in enumerate(results, start=1):
            print(f"[{index}] {item.arxiv_id}")
            print("title:", item.title)
            print("authors:", ", ".join(item.authors))
            print("published:", item.published)
            print("pdf_url:", item.pdf_url)
            print()
        return

    if not args.value:
        raise SystemExit("Provide an arXiv id/URL or use --search.")

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
