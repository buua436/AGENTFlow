from __future__ import annotations

import argparse
from pathlib import Path

from agentflow import MinerUConfig, MinerUParser


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to the input document")
    parser.add_argument("--output-dir", help="Directory for extracted MinerU output")
    parser.add_argument("--lang", action="append", dest="langs", help="Language code, repeatable")
    parser.add_argument(
        "--server-url",
        help="Use an existing MinerU API server instead of starting a local one",
    )
    args = parser.parse_args()

    input_path = Path(args.file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    langs = tuple(args.langs) if args.langs else ("ch", "en")

    mineru = MinerUParser(
        MinerUConfig(
            lang_list=langs,
            backend="pipeline",
            parse_method="auto",
            server_url=args.server_url,
        )
    )

    try:
        result = mineru.parse_file(input_path, output_dir=output_dir)
    finally:
        mineru.stop()

    print("task_id:", result.task_id)
    print("output_dir:", result.output_dir)
    print("markdown_files:")
    for path in result.markdown_files:
        print("  ", path)
    print("middle_json_files:")
    for path in result.middle_json_files:
        print("  ", path)
    print("content_list_files:")
    for path in result.content_list_files:
        print("  ", path)


if __name__ == "__main__":
    main()
