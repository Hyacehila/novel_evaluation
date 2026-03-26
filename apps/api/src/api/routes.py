from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status

from .dependencies import get_evaluation_service
from .errors import ApiError
from packages.application.services.evaluation_service import EvaluationService
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.output.envelope import SuccessEnvelope
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.task import EvaluationTask


router = APIRouter(prefix="/api")


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    request: JointSubmissionRequest,
    background_tasks: BackgroundTasks,
    service: EvaluationService = Depends(get_evaluation_service),
) -> SuccessEnvelope[EvaluationTask]:
    task = service.create_task(request)
    background_tasks.add_task(service.execute_task, task.taskId)
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
    service: EvaluationService = Depends(get_evaluation_service),
):
    history = service.get_history()
    return SuccessEnvelope(data=history, meta=history.meta)
