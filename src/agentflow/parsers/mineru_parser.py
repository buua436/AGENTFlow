"""MinerU parser wrapper for AGENTFlow."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from mineru.cli.common import aio_do_parse, do_parse, read_fn


StatusCallback = Callable[[str], Any]


@dataclass(slots=True)
class MinerUConfig:
    """Default MinerU parse configuration for direct local invocation."""

    backend: str = "pipeline"
    parse_method: str = "auto"
    lang_list: tuple[str, ...] = ("ch",)
    formula_enable: bool = True
    table_enable: bool = True
    server_url: str | None = None
    start_page_id: int = 0
    end_page_id: int | None = None
    return_md: bool = True
    return_middle_json: bool = True
    return_model_output: bool = False
    return_content_list: bool = True
    return_original_file: bool = False
    draw_layout_bbox: bool = False
    draw_span_bbox: bool = False


@dataclass(slots=True)
class MinerUParseResult:
    """Normalized parse result for one file."""

    task_id: str
    source_name: str
    source_path: Path | None
    output_dir: Path
    parse_dir: Path
    backend: str
    parse_method: str
    extracted_files: tuple[Path, ...]
    markdown_files: tuple[Path, ...]
    middle_json_files: tuple[Path, ...]
    content_list_files: tuple[Path, ...]
    content_list_v2_files: tuple[Path, ...]
    model_output_files: tuple[Path, ...]
    original_files: tuple[Path, ...]
    file_names: tuple[str, ...]
    queued_ahead: int | None
    raw: Any

    @property
    def markdown_file(self) -> Path | None:
        return self.markdown_files[0] if self.markdown_files else None

    @property
    def middle_json_file(self) -> Path | None:
        return self.middle_json_files[0] if self.middle_json_files else None

    @property
    def content_list_file(self) -> Path | None:
        return self.content_list_files[0] if self.content_list_files else None


class MinerUError(RuntimeError):
    """Raised when a MinerU parse request fails."""


class MinerUParser:
    """Thin wrapper around MinerU direct local parsing."""

    def __init__(self, config: MinerUConfig | None = None) -> None:
        self.config = config or MinerUConfig()

    def parse_file(
        self,
        file_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        lang: str | None = None,
        lang_list: list[str] | tuple[str, ...] | None = None,
        backend: str | None = None,
        parse_method: str | None = None,
        status_callback: StatusCallback | None = None,
        **kwargs: Any,
    ) -> MinerUParseResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise MinerUError(
                "parse_file() cannot be used inside a running event loop. "
                "Use aparse_file() instead."
            )
        return asyncio.run(
            self.aparse_file(
                file_path,
                output_dir=output_dir,
                lang=lang,
                lang_list=lang_list,
                backend=backend,
                parse_method=parse_method,
                status_callback=status_callback,
                **kwargs,
            )
        )

    async def aparse_file(
        self,
        file_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        lang: str | None = None,
        lang_list: list[str] | tuple[str, ...] | None = None,
        backend: str | None = None,
        parse_method: str | None = None,
        status_callback: StatusCallback | None = None,
        **kwargs: Any,
    ) -> MinerUParseResult:
        source_path = Path(file_path).expanduser().resolve()
        if not source_path.exists() or not source_path.is_file():
            raise MinerUError(f"Input file not found: {source_path}")

        await self._emit_status(status_callback, "reading")
        try:
            file_bytes = await asyncio.to_thread(read_fn, source_path)
        except Exception as exc:
            raise MinerUError(str(exc)) from exc

        return await self._aparse_document(
            file_bytes=file_bytes,
            source_name=source_path.name,
            source_path=source_path,
            output_dir=output_dir,
            lang=lang,
            lang_list=lang_list,
            backend=backend,
            parse_method=parse_method,
            status_callback=status_callback,
            **kwargs,
        )

    def parse_bytes(
        self,
        file_bytes: bytes,
        *,
        file_name: str = "document.pdf",
        output_dir: str | Path | None = None,
        lang: str | None = None,
        lang_list: list[str] | tuple[str, ...] | None = None,
        backend: str | None = None,
        parse_method: str | None = None,
        status_callback: StatusCallback | None = None,
        **kwargs: Any,
    ) -> MinerUParseResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise MinerUError(
                "parse_bytes() cannot be used inside a running event loop. "
                "Use aparse_bytes() instead."
            )
        return asyncio.run(
            self.aparse_bytes(
                file_bytes,
                file_name=file_name,
                output_dir=output_dir,
                lang=lang,
                lang_list=lang_list,
                backend=backend,
                parse_method=parse_method,
                status_callback=status_callback,
                **kwargs,
            )
        )

    async def aparse_bytes(
        self,
        file_bytes: bytes,
        *,
        file_name: str = "document.pdf",
        output_dir: str | Path | None = None,
        lang: str | None = None,
        lang_list: list[str] | tuple[str, ...] | None = None,
        backend: str | None = None,
        parse_method: str | None = None,
        status_callback: StatusCallback | None = None,
        **kwargs: Any,
    ) -> MinerUParseResult:
        if not isinstance(file_bytes, (bytes, bytearray)):
            raise MinerUError("file_bytes must be bytes-like.")

        return await self._aparse_document(
            file_bytes=bytes(file_bytes),
            source_name=file_name,
            source_path=None,
            output_dir=output_dir,
            lang=lang,
            lang_list=lang_list,
            backend=backend,
            parse_method=parse_method,
            status_callback=status_callback,
            **kwargs,
        )

    async def _aparse_document(
        self,
        *,
        file_bytes: bytes,
        source_name: str,
        source_path: Path | None,
        output_dir: str | Path | None,
        lang: str | None,
        lang_list: list[str] | tuple[str, ...] | None,
        backend: str | None,
        parse_method: str | None,
        status_callback: StatusCallback | None,
        **kwargs: Any,
    ) -> MinerUParseResult:
        source_stem = Path(source_name).stem or "document"
        target_dir = self._resolve_output_dir(source_path, source_stem, output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        options = self._build_options(
            lang=lang,
            lang_list=lang_list,
            backend=backend,
            parse_method=parse_method,
            kwargs=kwargs,
        )
        parse_kwargs = self._build_parse_kwargs(options)
        file_names = [source_stem]
        payloads = [file_bytes]
        langs_for_mineru = [options["lang"]]

        await self._emit_status(status_callback, "parsing")
        try:
            if options["backend"] == "pipeline":
                await asyncio.to_thread(
                    do_parse,
                    str(target_dir),
                    file_names,
                    payloads,
                    langs_for_mineru,
                    **parse_kwargs,
                )
            else:
                await aio_do_parse(
                    str(target_dir),
                    file_names,
                    payloads,
                    langs_for_mineru,
                    **parse_kwargs,
                )
        except Exception as exc:
            raise MinerUError(str(exc)) from exc

        await self._emit_status(status_callback, "collecting")
        result = self._build_result(
            source_name=source_name,
            source_path=source_path,
            source_stem=source_stem,
            output_dir=target_dir,
            backend=options["backend"],
            parse_method=options["parse_method"],
        )
        await self._emit_status(status_callback, "completed")
        return result

    def stop(self) -> None:
        """Backward-compatible no-op kept for callers from the old API mode."""
        return None

    def _build_options(
        self,
        *,
        lang: str | None,
        lang_list: list[str] | tuple[str, ...] | None,
        backend: str | None,
        parse_method: str | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        if lang is not None and lang_list is not None:
            raise MinerUError("Use either `lang` or `lang_list`, not both.")

        effective_lang_list = tuple(lang_list) if lang_list is not None else self.config.lang_list
        effective_lang = lang or (effective_lang_list[0] if effective_lang_list else "ch")
        if not effective_lang:
            raise MinerUError("A non-empty language value is required.")

        options = {
            "lang": effective_lang,
            "backend": backend or self.config.backend,
            "parse_method": parse_method or self.config.parse_method,
            "formula_enable": kwargs.pop("formula_enable", self.config.formula_enable),
            "table_enable": kwargs.pop("table_enable", self.config.table_enable),
            "server_url": kwargs.pop("server_url", self.config.server_url),
            "start_page_id": kwargs.pop("start_page_id", self.config.start_page_id),
            "end_page_id": kwargs.pop("end_page_id", self.config.end_page_id),
            "return_md": kwargs.pop("return_md", self.config.return_md),
            "return_middle_json": kwargs.pop(
                "return_middle_json", self.config.return_middle_json
            ),
            "return_model_output": kwargs.pop(
                "return_model_output", self.config.return_model_output
            ),
            "return_content_list": kwargs.pop(
                "return_content_list", self.config.return_content_list
            ),
            "return_original_file": kwargs.pop(
                "return_original_file", self.config.return_original_file
            ),
            "draw_layout_bbox": kwargs.pop(
                "draw_layout_bbox", self.config.draw_layout_bbox
            ),
            "draw_span_bbox": kwargs.pop(
                "draw_span_bbox", self.config.draw_span_bbox
            ),
        }
        if kwargs:
            raise MinerUError(f"Unsupported MinerU parse options: {sorted(kwargs)}")
        return options

    @staticmethod
    def _build_parse_kwargs(options: dict[str, Any]) -> dict[str, Any]:
        return {
            "backend": options["backend"],
            "parse_method": options["parse_method"],
            "formula_enable": options["formula_enable"],
            "table_enable": options["table_enable"],
            "server_url": options["server_url"],
            "f_draw_layout_bbox": options["draw_layout_bbox"],
            "f_draw_span_bbox": options["draw_span_bbox"],
            "f_dump_md": options["return_md"],
            "f_dump_middle_json": options["return_middle_json"],
            "f_dump_model_output": options["return_model_output"],
            "f_dump_orig_pdf": options["return_original_file"],
            "f_dump_content_list": options["return_content_list"],
            "start_page_id": options["start_page_id"],
            "end_page_id": options["end_page_id"],
        }

    @staticmethod
    def _resolve_output_dir(
        source_path: Path | None,
        source_stem: str,
        output_dir: str | Path | None,
    ) -> Path:
        if output_dir is not None:
            return Path(output_dir).expanduser().resolve()
        if source_path is not None:
            return source_path.parent / f"{source_stem}_mineru"
        return Path.cwd() / f"{source_stem}_mineru"

    @classmethod
    def _build_result(
        cls,
        *,
        source_name: str,
        source_path: Path | None,
        source_stem: str,
        output_dir: Path,
        backend: str,
        parse_method: str,
    ) -> MinerUParseResult:
        extracted_files = tuple(
            path for path in sorted(output_dir.rglob("*")) if path.is_file()
        )
        parse_dir = cls._resolve_parse_dir(output_dir, source_stem, backend, parse_method)
        return MinerUParseResult(
            task_id=f"local-{uuid4().hex[:12]}",
            source_name=source_name,
            source_path=source_path,
            output_dir=output_dir,
            parse_dir=parse_dir,
            backend=backend,
            parse_method=parse_method,
            extracted_files=extracted_files,
            markdown_files=cls._match_files(extracted_files, ".md"),
            middle_json_files=cls._match_files(extracted_files, "_middle.json"),
            content_list_files=cls._match_files(extracted_files, "_content_list.json"),
            content_list_v2_files=cls._match_files(extracted_files, "_content_list_v2.json"),
            model_output_files=cls._match_files(extracted_files, "_model.json"),
            original_files=tuple(
                path for path in extracted_files if "_origin." in path.name
            ),
            file_names=(source_stem,),
            queued_ahead=None,
            raw={
                "mode": "local",
                "backend": backend,
                "parse_method": parse_method,
                "parse_dir": str(parse_dir),
                "source_name": source_name,
                "source_path": None if source_path is None else str(source_path),
            },
        )

    @staticmethod
    async def _emit_status(
        status_callback: StatusCallback | None,
        status: str,
    ) -> None:
        if status_callback is None:
            return
        result = status_callback(status)
        if asyncio.iscoroutine(result):
            await result

    @staticmethod
    def _match_files(files: tuple[Path, ...], suffix: str) -> tuple[Path, ...]:
        return tuple(path for path in files if path.name.endswith(suffix))

    @staticmethod
    def _resolve_parse_dir(
        output_dir: Path,
        file_stem: str,
        backend: str,
        parse_method: str,
    ) -> Path:
        if backend.startswith("pipeline"):
            return output_dir / file_stem / parse_method
        if backend.startswith("vlm"):
            return output_dir / file_stem / "vlm"
        if backend.startswith("hybrid"):
            return output_dir / file_stem / f"hybrid_{parse_method}"
        return output_dir / file_stem


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to the input document")
    parser.add_argument("--output-dir", help="Directory for extracted MinerU output")
    parser.add_argument("--lang", default="ch", help="Primary language for the document")
    parser.add_argument(
        "--backend",
        default="pipeline",
        help="MinerU backend, for example pipeline or hybrid-auto-engine",
    )
    parser.add_argument(
        "--parse-method",
        default="auto",
        help="MinerU parse method, for example auto, txt, or ocr",
    )
    parser.add_argument(
        "--server-url",
        help="Server URL used only by MinerU http-client style backends",
    )
    args = parser.parse_args()

    input_path = Path(args.file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    mineru = MinerUParser(
        MinerUConfig(
            lang_list=(args.lang,),
            backend=args.backend,
            parse_method=args.parse_method,
            server_url=args.server_url,
        )
    )

    result = mineru.parse_file(input_path, output_dir=output_dir)

    print("task_id:", result.task_id)
    print("source_name:", result.source_name)
    print("output_dir:", result.output_dir)
    print("parse_dir:", result.parse_dir)
    print("backend:", result.backend)
    print("parse_method:", result.parse_method)
    print("markdown_files:")
    for path in result.markdown_files:
        print("  ", path)
    print("middle_json_files:")
    for path in result.middle_json_files:
        print("  ", path)
    print("content_list_files:")
    for path in result.content_list_files:
        print("  ", path)
    print("content_list_v2_files:")
    for path in result.content_list_v2_files:
        print("  ", path)
    print("model_output_files:")
    for path in result.model_output_files:
        print("  ", path)


if __name__ == "__main__":
    _main()
