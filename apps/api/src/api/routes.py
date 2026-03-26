from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException

from packages.application.services.evaluation_service import EvaluationService
from packages.schemas.common.enums import TaskStatus
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.output.envelope import SuccessEnvelope
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.task import EvaluationTask

from .dependencies import get_evaluation_service
from .errors import ApiError
from .upload_parsing import build_upload_request, read_upload_text, resolve_upload_max_bytes


router = APIRouter(prefix="/api")


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    request: Request,
    background_tasks: BackgroundTasks,
    service: EvaluationService = Depends(get_evaluation_service),
) -> SuccessEnvelope[EvaluationTask]:
    submission = await _parse_submission_request(request)
    task = service.create_task(submission)
    background_tasks.add_task(service.execute_task, task.taskId, submission)
    return SuccessEnvelope(data=task)


@router.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    service: EvaluationService = Depends(get_evaluation_service),
) -> SuccessEnvelope[EvaluationTask]:
    try:
        task = service.get_task(task_id)
    except LookupError as exc:
        raise ApiError(status_code=404, code=ErrorCode.TASK_NOT_FOUND, message="任务不存在") from exc
    return SuccessEnvelope(data=task)


@router.get("/tasks/{task_id}/result")
def get_result(
    task_id: str,
    service: EvaluationService = Depends(get_evaluation_service),
):
    try:
        result = service.get_result(task_id)
    except LookupError as exc:
        raise ApiError(status_code=404, code=ErrorCode.TASK_NOT_FOUND, message="任务不存在") from exc
    return SuccessEnvelope(data=result)


@router.get("/dashboard")
def get_dashboard(
    service: EvaluationService = Depends(get_evaluation_service),
):
    return SuccessEnvelope(data=service.get_dashboard())


@router.get("/history")
def get_history(
    q: str | None = Query(default=None),
    status: TaskStatus | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    service: EvaluationService = Depends(get_evaluation_service),
):
    try:
        history = service.get_history(q=q, status=status, cursor=cursor, limit=limit)
    except ValueError as exc:
        raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法") from exc
    return SuccessEnvelope(data=history, meta=history.meta)


async def _parse_submission_request(request: Request) -> JointSubmissionRequest:
    if _is_multipart_request(request):
        return await _parse_multipart_submission(request)
    return await _parse_json_submission(request)


async def _parse_json_submission(request: Request) -> JointSubmissionRequest:
    try:
        payload = await request.json()
        return JointSubmissionRequest.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法") from exc


async def _parse_multipart_submission(request: Request) -> JointSubmissionRequest:
    try:
        max_bytes = resolve_upload_max_bytes()
    except ValueError as exc:
        raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法") from exc

    try:
        form = await request.form(max_files=2, max_fields=2, max_part_size=max_bytes)
    except StarletteHTTPException as exc:
        detail = str(exc.detail)
        if "Part exceeded maximum size" in detail:
            raise ApiError(status_code=422, code=ErrorCode.UPLOAD_TOO_LARGE, message="上传文件超过大小限制") from exc
        raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法") from exc
    except MultiPartException as exc:
        raise ApiError(status_code=422, code=ErrorCode.UPLOAD_TOO_LARGE, message="上传文件超过大小限制") from exc

    chapters_upload = _get_optional_upload(form.get("chaptersFile"), field_name="chaptersFile")
    outline_upload = _get_optional_upload(form.get("outlineFile"), field_name="outlineFile")
    chapters_text = await read_upload_text(chapters_upload, max_bytes=max_bytes)
    outline_text = await read_upload_text(outline_upload, max_bytes=max_bytes)
    return build_upload_request(
        title=_get_optional_text(form.get("title")),
        source_type=_get_optional_text(form.get("sourceType")),
        chapters_text=chapters_text,
        outline_text=outline_text,
    )


def _is_multipart_request(request: Request) -> bool:
    content_type = request.headers.get("content-type", "").lower()
    return content_type.startswith("multipart/form-data")


def _get_optional_upload(value: Any, *, field_name: str) -> UploadFile | None:
    if value is None or value == "":
        return None
    if isinstance(value, UploadFile):
        return value
    raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message=f"{field_name} 输入参数不合法")


def _get_optional_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    raise ApiError(status_code=422, code=ErrorCode.VALIDATION_ERROR, message="输入参数不合法")
