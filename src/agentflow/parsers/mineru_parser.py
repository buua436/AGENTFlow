"""MinerU parser wrapper for AGENTFlow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from mineru.cli.api_client import (
    ReusableLocalAPIServer,
    UploadAsset,
    build_parse_request_form_data,
    build_http_timeout,
    download_result_zip,
    safe_extract_zip,
    submit_parse_task_sync,
    wait_for_task_result,
)


@dataclass(slots=True)
class MinerUConfig:
    """Default MinerU parse configuration."""

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
    return_images: bool = True
    response_format_zip: bool = True
    return_original_file: bool = False
    timeout_seconds: float = 300.0
    local_api_extra_cli_args: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class MinerUParseResult:
    """Normalized parse result for one file."""

    task_id: str
    output_dir: Path
    extracted_files: tuple[Path, ...]
    markdown_files: tuple[Path, ...]
    middle_json_files: tuple[Path, ...]
    content_list_files: tuple[Path, ...]
    file_names: tuple[str, ...]
    queued_ahead: int | None
    raw: Any


class MinerUError(RuntimeError):
    """Raised when a MinerU parse request fails."""


class MinerUParser:
    """Thin wrapper around the MinerU local API workflow."""

    def __init__(self, config: MinerUConfig | None = None) -> None:
        self.config = config or MinerUConfig()
        self._local_server = ReusableLocalAPIServer(
            extra_cli_args=self.config.local_api_extra_cli_args
        )

    def parse_file(
        self,
        file_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        lang_list: list[str] | tuple[str, ...] | None = None,
        backend: str | None = None,
        parse_method: str | None = None,
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
                lang_list=lang_list,
                backend=backend,
                parse_method=parse_method,
                **kwargs,
            )
        )

    async def aparse_file(
        self,
        file_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        lang_list: list[str] | tuple[str, ...] | None = None,
        backend: str | None = None,
        parse_method: str | None = None,
        status_callback: Any | None = None,
        **kwargs: Any,
    ) -> MinerUParseResult:
        source_path = Path(file_path).expanduser().resolve()
        if not source_path.exists() or not source_path.is_file():
            raise MinerUError(f"Input file not found: {source_path}")

        target_dir = (
            Path(output_dir).expanduser().resolve()
            if output_dir is not None
            else source_path.parent / f"{source_path.stem}_mineru"
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        base_url = self._resolve_base_url()
        form_data = build_parse_request_form_data(
            lang_list=tuple(lang_list) if lang_list is not None else self.config.lang_list,
            backend=backend or self.config.backend,
            parse_method=parse_method or self.config.parse_method,
            formula_enable=kwargs.pop("formula_enable", self.config.formula_enable),
            table_enable=kwargs.pop("table_enable", self.config.table_enable),
            server_url=kwargs.pop("server_url", self.config.server_url),
            start_page_id=kwargs.pop("start_page_id", self.config.start_page_id),
            end_page_id=kwargs.pop("end_page_id", self.config.end_page_id),
            return_md=kwargs.pop("return_md", self.config.return_md),
            return_middle_json=kwargs.pop(
                "return_middle_json", self.config.return_middle_json
            ),
            return_model_output=kwargs.pop(
                "return_model_output", self.config.return_model_output
            ),
            return_content_list=kwargs.pop(
                "return_content_list", self.config.return_content_list
            ),
            return_images=kwargs.pop("return_images", self.config.return_images),
            response_format_zip=kwargs.pop(
                "response_format_zip", self.config.response_format_zip
            ),
            return_original_file=kwargs.pop(
                "return_original_file", self.config.return_original_file
            ),
        )
        if kwargs:
            raise MinerUError(f"Unsupported MinerU parse options: {sorted(kwargs)}")

        upload_asset = UploadAsset(path=source_path, upload_name=source_path.name)
        try:
            submit_response = submit_parse_task_sync(
                base_url=base_url,
                upload_assets=[upload_asset],
                form_data=form_data,
            )
            async with httpx.AsyncClient(
                timeout=build_http_timeout(),
                follow_redirects=True,
            ) as client:
                await wait_for_task_result(
                    client,
                    submit_response,
                    task_label=source_path.name,
                    status_callback=status_callback,
                    timeout_seconds=self.config.timeout_seconds,
                )
                zip_path = await download_result_zip(
                    client,
                    submit_response,
                    task_label=source_path.name,
                )
        except Exception as exc:
            raise MinerUError(str(exc)) from exc

        try:
            safe_extract_zip(zip_path, target_dir)
        except Exception as exc:
            raise MinerUError(str(exc)) from exc
        finally:
            zip_path.unlink(missing_ok=True)

        extracted_files = tuple(
            path for path in sorted(target_dir.rglob("*")) if path.is_file()
        )
        return MinerUParseResult(
            task_id=submit_response.task_id,
            output_dir=target_dir,
            extracted_files=extracted_files,
            markdown_files=self._match_files(extracted_files, ".md"),
            middle_json_files=self._match_files(extracted_files, "_middle.json"),
            content_list_files=self._match_files(extracted_files, "_content_list.json"),
            file_names=submit_response.file_names,
            queued_ahead=submit_response.queued_ahead,
            raw=submit_response,
        )

    def stop(self) -> None:
        self._local_server.stop()

    def _resolve_base_url(self) -> str:
        if self.config.server_url:
            return self.config.server_url.rstrip("/")
        server, _ = self._local_server.ensure_started()
        if server.base_url is None:
            raise MinerUError("Failed to start local MinerU API server.")
        return server.base_url.rstrip("/")

    @staticmethod
    def _match_files(files: tuple[Path, ...], suffix: str) -> tuple[Path, ...]:
        return tuple(path for path in files if path.name.endswith(suffix))
