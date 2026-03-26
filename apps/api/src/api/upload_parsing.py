from __future__ import annotations

import logging
import os
from io import BytesIO
from pathlib import Path

from docx import Document
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from packages.schemas.common.enums import SubmissionSourceType
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.output.error import ErrorCode

from .errors import ApiError

logger = logging.getLogger(__name__)

DEFAULT_UPLOAD_MAX_BYTES = 10 * 1024 * 1024
_UPLOAD_READ_CHUNK_SIZE = 64 * 1024
_SUPPORTED_UPLOAD_SUFFIXES = frozenset({".txt", ".md", ".docx"})


def resolve_upload_max_bytes() -> int:
    raw_value = os.getenv("NOVEL_EVAL_UPLOAD_MAX_BYTES")
    if raw_value is None or not raw_value.strip():
        return DEFAULT_UPLOAD_MAX_BYTES
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError("NOVEL_EVAL_UPLOAD_MAX_BYTES 必须是整数。") from exc
    if value <= 0:
        raise ValueError("NOVEL_EVAL_UPLOAD_MAX_BYTES 必须大于 0。")
    return value


async def read_upload_text(upload: UploadFile | None, *, max_bytes: int | None = None) -> str | None:
    if upload is None:
        return None
    filename = upload.filename or ""
    if not filename:
        await upload.close()
        raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法")
    limit = max_bytes or DEFAULT_UPLOAD_MAX_BYTES
    content = bytearray()
    try:
        while chunk := await upload.read(_UPLOAD_READ_CHUNK_SIZE):
            content.extend(chunk)
            if len(content) > limit:
                raise ApiError(status_code=422, code=ErrorCode.UPLOAD_TOO_LARGE, message="上传文件超过大小限制")
    finally:
        await upload.close()
    return parse_upload_bytes(filename=filename, content=bytes(content), max_bytes=limit)


def parse_upload_bytes(*, filename: str, content: bytes, max_bytes: int | None = None) -> str:
    limit = max_bytes or DEFAULT_UPLOAD_MAX_BYTES
    if len(content) > limit:
        raise ApiError(status_code=422, code=ErrorCode.UPLOAD_TOO_LARGE, message="上传文件超过大小限制")

    suffix = Path(filename).suffix.lower()
    if suffix not in _SUPPORTED_UPLOAD_SUFFIXES:
        raise ApiError(status_code=422, code=ErrorCode.UNSUPPORTED_UPLOAD_FORMAT, message="上传文件格式不受支持")

    if suffix == ".docx":
        return _parse_docx_text(content)
    return _parse_text_content(content)


def build_upload_request(
    *,
    title: str,
    source_type: str,
    chapters_text: str | None,
    outline_text: str | None,
) -> JointSubmissionRequest:
    if chapters_text is None and outline_text is None:
        raise ApiError(status_code=422, code=ErrorCode.EMPTY_SUBMISSION, message="chapters 与 outline 至少存在一侧")

    try:
        submission_source = SubmissionSourceType(source_type)
    except ValueError as exc:
        raise ApiError(status_code=422, code=ErrorCode.INVALID_SOURCE_TYPE, message="sourceType 不合法") from exc

    try:
        return JointSubmissionRequest(
            title=title,
            chapters=[ManuscriptChapter(content=chapters_text)] if chapters_text is not None else None,
            outline=ManuscriptOutline(content=outline_text) if outline_text is not None else None,
            sourceType=submission_source,
        )
    except ValidationError as exc:
        raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法") from exc


def _parse_text_content(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise ApiError(status_code=422, code=ErrorCode.UPLOAD_PARSE_FAILED, message="上传文件解析失败") from exc


def _parse_docx_text(content: bytes) -> str:
    try:
        document = Document(BytesIO(content))
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        raise ApiError(status_code=422, code=ErrorCode.UPLOAD_PARSE_FAILED, message="上传文件解析失败") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("DOCX 解析出现未预期错误")
        raise ApiError(status_code=422, code=ErrorCode.UPLOAD_PARSE_FAILED, message="上传文件解析失败") from exc

    paragraphs = [paragraph.text.replace("\r\n", "\n").replace("\r", "\n") for paragraph in document.paragraphs]
    while paragraphs and not paragraphs[0]:
        paragraphs.pop(0)
    while paragraphs and not paragraphs[-1]:
        paragraphs.pop()
    return "\n".join(paragraphs)
