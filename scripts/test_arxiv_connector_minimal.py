from __future__ import annotations

import argparse
from pathlib import Path

from agentflow import ArxivConnector


def main() -> None:
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
    main()
