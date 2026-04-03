from __future__ import annotations

import base64
import binascii
import logging
from dataclasses import dataclass
from datetime import datetime

from packages.application.ports.runtime_metadata import PromptRuntimePort, ProviderExecutionPort
from packages.application.ports.task_repository import TaskRepository
from packages.application.scoring_pipeline.exceptions import PipelineBlockedError, PipelineFailureError
from packages.application.scoring_pipeline.orchestration import ScoringPipeline
from packages.application.support.clock import Clock, UtcClock
from packages.application.support.id_generator import IdGenerator, UuidTaskIdGenerator
from packages.schemas.common.base import MetaData
from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    FatalRisk,
    InputComposition,
    ResultStatus,
    ScoreBand,
    StageName,
    StageStatus,
    Sufficiency,
    TaskStatus,
)
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.dashboard import DashboardSummary, HistoryList
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.result import (
    AxisEvaluationResult,
    EvaluationResult,
    EvaluationResultResource,
    FinalEvaluationProjection,
    OverallEvaluationResult,
)
from packages.schemas.output.task import EvaluationTask, EvaluationTaskSummary, RecentResultSummary
from packages.schemas.stages.aggregation import PlatformCandidate
from packages.schemas.stages.type_classification import TypeClassificationResult
from packages.runtime.logging import log_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RuntimeMetadata:
    schema_version: str
    prompt_version: str
    rubric_version: str
    provider_id: str
    model_id: str


class EvaluationService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        prompt_runtime: PromptRuntimePort | None = None,
        provider_adapter: ProviderExecutionPort | None = None,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._task_repository = task_repository
        self._prompt_runtime = prompt_runtime
        self._provider_adapter = provider_adapter
        self._id_generator = id_generator or UuidTaskIdGenerator()
        self._clock = clock or UtcClock()
        self._scoring_pipeline = (
            ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider_adapter)
            if prompt_runtime is not None and provider_adapter is not None
            else None
        )

    def create_task(self, request: JointSubmissionRequest) -> EvaluationTask:
        task_id = self._id_generator.new_task_id()
        now = self._clock.now()
        screening = self._build_input_screening(task_id, request)
        task = EvaluationTask(
            taskId=task_id,
            title=request.title,
            inputSummary=self._build_input_summary(request),
            inputComposition=request.inputComposition,
            hasChapters=request.hasChapters,
            hasOutline=request.hasOutline,
            evaluationMode=screening.evaluationMode,
            status=TaskStatus.QUEUED,
            resultStatus=ResultStatus.NOT_AVAILABLE,
            schemaVersion=screening.schemaVersion,
            promptVersion=screening.promptVersion,
            rubricVersion=screening.rubricVersion,
            providerId=screening.providerId,
            modelId=screening.modelId,
            createdAt=now,
            updatedAt=now,
        )
        created = self._task_repository.create_task(task)
        log_event(
            logger,
            logging.INFO,
            "task_created",
            taskId=created.taskId,
            stage="task_create",
            promptVersion=created.promptVersion,
            schemaVersion=created.schemaVersion,
            rubricVersion=created.rubricVersion,
            providerId=created.providerId,
            modelId=created.modelId,
            resultStatus=created.resultStatus,
        )
        return created

    def get_task(self, task_id: str) -> EvaluationTask:
        task = self._task_repository.get_task(task_id)
        if task is None:
            raise LookupError("任务不存在")
        return self._normalize_task_result_status(task)

    def start_task(self, task_id: str) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.QUEUED:
            raise ValueError("只有 queued 状态可以开始执行。")
        now = self._clock.now()
        updated = task.model_copy(
            update={
                "status": TaskStatus.PROCESSING,
                "startedAt": now,
                "updatedAt": now,
            }
        )
        log_event(
            logger,
            logging.INFO,
            "task_started",
            taskId=updated.taskId,
            stage="task_start",
            promptVersion=updated.promptVersion,
            schemaVersion=updated.schemaVersion,
            rubricVersion=updated.rubricVersion,
            providerId=updated.providerId,
            modelId=updated.modelId,
            resultStatus=updated.resultStatus,
        )
        return self._task_repository.update_task(updated)

    def complete_task_with_result(
        self,
        task_id: str,
        *,
        signing_probability: int,
        commercial_value: int,
        writing_quality: int,
        innovation_score: int,
    ) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.PROCESSING:
            raise ValueError("只有 processing 状态可以完成。")
        now = self._clock.now()
        projection = self._build_final_projection(
            task,
            signing_probability=signing_probability,
            commercial_value=commercial_value,
            writing_quality=writing_quality,
            innovation_score=innovation_score,
        )
        result = self._build_result_from_projection(projection, result_time=now)
        resource = EvaluationResultResource(
            taskId=task.taskId,
            resultStatus=ResultStatus.AVAILABLE,
            resultTime=now,
            result=result,
            message=None,
        )
        self._task_repository.save_result(task.taskId, resource)
        updated = task.model_copy(
            update={
                "status": TaskStatus.COMPLETED,
                "resultStatus": ResultStatus.AVAILABLE,
                "completedAt": now,
                "updatedAt": now,
            }
        )
        return self._task_repository.update_task(updated)

    def complete_task_with_projection(
        self,
        task_id: str,
        *,
        projection: FinalEvaluationProjection,
    ) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.PROCESSING:
            raise ValueError("只有 processing 状态可以完成。")
        now = self._clock.now()
        result = self._build_result_from_projection(projection, result_time=now)
        resource = EvaluationResultResource(
            taskId=task.taskId,
            resultStatus=ResultStatus.AVAILABLE,
            resultTime=now,
            result=result,
            message=None,
        )
        self._task_repository.save_result(task.taskId, resource)
        updated = task.model_copy(
            update={
                "status": TaskStatus.COMPLETED,
                "resultStatus": ResultStatus.AVAILABLE,
                "schemaVersion": projection.schemaVersion,
                "promptVersion": projection.promptVersion,
                "rubricVersion": projection.rubricVersion,
                "providerId": projection.providerId,
                "modelId": projection.modelId,
                "novelType": projection.typeAssessment.novelType if projection.typeAssessment is not None else task.novelType,
                "typeClassificationConfidence": (
                    projection.typeAssessment.classificationConfidence
                    if projection.typeAssessment is not None
                    else task.typeClassificationConfidence
                ),
                "typeFallbackUsed": (
                    projection.typeAssessment.fallbackUsed
                    if projection.typeAssessment is not None
                    else task.typeFallbackUsed
                ),
                "completedAt": now,
                "updatedAt": now,
            }
        )
        log_event(
            logger,
            logging.INFO,
            "task_completed",
            taskId=updated.taskId,
            stage=StageName.FINAL_PROJECTION,
            promptVersion=projection.promptVersion,
            schemaVersion=projection.schemaVersion,
            rubricVersion=projection.rubricVersion,
            providerId=projection.providerId,
            modelId=projection.modelId,
            resultStatus=updated.resultStatus,
        )
        return self._task_repository.update_task(updated)

    def block_task(self, task_id: str, *, error_code: ErrorCode, error_message: str) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.PROCESSING:
            raise ValueError("只有 processing 状态可以阻断结束。")
        now = self._clock.now()
        resource = EvaluationResultResource(
            taskId=task.taskId,
            resultStatus=ResultStatus.BLOCKED,
            resultTime=None,
            result=None,
            message="结果未满足正式展示条件",
        )
        self._task_repository.save_result(task.taskId, resource)
        updated = task.model_copy(
            update={
                "status": TaskStatus.COMPLETED,
                "resultStatus": ResultStatus.BLOCKED,
                "errorCode": error_code,
                "errorMessage": error_message,
                "completedAt": now,
                "updatedAt": now,
            }
        )
        log_event(
            logger,
            logging.WARNING,
            "task_blocked",
            taskId=updated.taskId,
            stage="task_terminal",
            promptVersion=updated.promptVersion,
            schemaVersion=updated.schemaVersion,
            rubricVersion=updated.rubricVersion,
            providerId=updated.providerId,
            modelId=updated.modelId,
            resultStatus=updated.resultStatus,
            errorCode=error_code,
        )
        return self._task_repository.update_task(updated)

    def fail_task(self, task_id: str, *, error_code: ErrorCode, error_message: str) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.PROCESSING:
            raise ValueError("只有 processing 状态可以失败结束。")
        now = self._clock.now()
        resource = EvaluationResultResource(
            taskId=task.taskId,
            resultStatus=ResultStatus.NOT_AVAILABLE,
            resultTime=None,
            result=None,
            message="结果尚未生成或当前不可展示",
        )
        self._task_repository.save_result(task.taskId, resource)
        updated = task.model_copy(
            update={
                "status": TaskStatus.FAILED,
                "resultStatus": ResultStatus.NOT_AVAILABLE,
                "errorCode": error_code,
                "errorMessage": error_message,
                "completedAt": now,
                "updatedAt": now,
            }
        )
        log_event(
            logger,
            logging.ERROR,
            "task_failed",
            taskId=updated.taskId,
            stage="task_terminal",
            promptVersion=updated.promptVersion,
            schemaVersion=updated.schemaVersion,
            rubricVersion=updated.rubricVersion,
            providerId=updated.providerId,
            modelId=updated.modelId,
            resultStatus=updated.resultStatus,
            errorCode=error_code,
        )
        return self._task_repository.update_task(updated)

    def get_result(self, task_id: str) -> EvaluationResultResource:
        self.get_task(task_id)
        result = self._task_repository.get_result(task_id)
        if result is not None:
            return result
        return EvaluationResultResource(
            taskId=task_id,
            resultStatus=ResultStatus.NOT_AVAILABLE,
            resultTime=None,
            result=None,
            message="结果尚未生成或当前不可展示",
        )

    def execute_task(self, task_id: str, submission: JointSubmissionRequest | None = None) -> None:
        try:
            self.start_task(task_id)
            if submission is None:
                raise ValueError("执行正式评分主线时必须提供 submission。")
            if self._scoring_pipeline is None:
                raise ValueError("当前 provider adapter 未接入正式执行接口。")
            task = self.get_task(task_id)
            screening = self._scoring_pipeline.run_screening(task=task, submission=submission)
            self._sync_task_with_screening(task_id, screening=screening)
            type_classification = self._scoring_pipeline.run_type_classification(
                task=self.get_task(task_id),
                submission=submission,
                screening=screening,
            )
            self.sync_task_with_type_classification(task_id, type_classification=type_classification)
            pipeline_result = self._scoring_pipeline.run_after_type_classification(
                task=self.get_task(task_id),
                submission=submission,
                screening=screening,
                type_classification=type_classification,
            )
            self.complete_task_with_projection(task_id, projection=pipeline_result.projection)
        except PipelineBlockedError as exc:
            self.block_task(
                task_id,
                error_code=exc.error_code,
                error_message=exc.message,
            )
        except PipelineFailureError as exc:
            task = self._task_repository.get_task(task_id)
            if task is None:
                return
            if task.status is TaskStatus.QUEUED:
                try:
                    self.start_task(task_id)
                except ValueError:
                    task = self._task_repository.get_task(task_id)
                    if task is None:
                        return
            task = self._task_repository.get_task(task_id)
            if task is None or task.status is not TaskStatus.PROCESSING:
                return
            self.fail_task(
                task_id,
                error_code=exc.error_code,
                error_message=exc.message,
            )
        except Exception:
            task = self._task_repository.get_task(task_id)
            logger.exception(
                "任务执行失败，task_id=%s status=%s",
                task_id,
                task.status.value if task is not None else "missing",
            )
            if task is None:
                return
            if task.status is TaskStatus.QUEUED:
                try:
                    self.start_task(task_id)
                except ValueError:
                    task = self._task_repository.get_task(task_id)
                    if task is None:
                        return
            task = self._task_repository.get_task(task_id)
            if task is None or task.status is not TaskStatus.PROCESSING:
                return
            self.fail_task(
                task_id,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_message="任务执行失败，结果当前不可用，请重新提交新任务。",
            )

    def _sync_task_with_screening(self, task_id: str, *, screening: InputScreeningResult) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.PROCESSING:
            raise ValueError("只有 processing 状态可以同步 screening 元数据。")
        now = self._clock.now()
        updated = task.model_copy(
            update={
                "evaluationMode": screening.evaluationMode,
                "schemaVersion": screening.schemaVersion,
                "promptVersion": screening.promptVersion,
                "rubricVersion": screening.rubricVersion,
                "providerId": screening.providerId,
                "modelId": screening.modelId,
                "updatedAt": now,
            }
        )
        return self._task_repository.update_task(updated)

    def sync_task_with_type_classification(
        self,
        task_id: str,
        *,
        type_classification: TypeClassificationResult,
    ) -> EvaluationTask:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.PROCESSING:
            raise ValueError("只有 processing 状态可以同步 type classification 元数据。")
        now = self._clock.now()
        updated = task.model_copy(
            update={
                "novelType": type_classification.novelType,
                "typeClassificationConfidence": type_classification.classificationConfidence,
                "typeFallbackUsed": type_classification.fallbackUsed,
                "schemaVersion": type_classification.schemaVersion,
                "promptVersion": type_classification.promptVersion,
                "rubricVersion": type_classification.rubricVersion,
                "providerId": type_classification.providerId,
                "modelId": type_classification.modelId,
                "updatedAt": now,
            }
        )
        return self._task_repository.update_task(updated)

    def recover_incomplete_tasks(self) -> None:
        stale_task_ids = [
            *self._task_repository.list_task_ids_by_status(TaskStatus.QUEUED),
            *self._task_repository.list_task_ids_by_status(TaskStatus.PROCESSING),
        ]
        for task_id in stale_task_ids:
            task = self.get_task(task_id)
            logger.warning(
                "恢复未完成任务为失败状态，task_id=%s status=%s",
                task_id,
                task.status.value,
            )
            if task.status is TaskStatus.QUEUED:
                self._task_repository.update_task(
                    task.model_copy(
                        update={
                            "status": TaskStatus.PROCESSING,
                            "startedAt": task.updatedAt,
                            "updatedAt": task.updatedAt,
                        }
                    )
                )
            self.fail_task(
                task_id,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_message="任务因进程重启中断，结果当前不可用，请重新提交新任务。",
            )

    def get_dashboard(self) -> DashboardSummary:
        tasks = [self._normalize_task_result_status(task) for task in self._task_repository.list_tasks()]
        summaries = [self._to_summary(task) for task in tasks]
        active = [summary for task, summary in zip(tasks, summaries) if task.status is TaskStatus.PROCESSING]
        recent_results = [
            RecentResultSummary(
                taskId=task.taskId,
                title=task.title,
                resultTime=result.resultTime,
                overallScore=result.result.overall.score,
                overallVerdict=result.result.overall.verdict,
            )
            for task in tasks
            if (result := self._task_repository.get_result(task.taskId)) is not None
            and result.result is not None
            and result.resultTime is not None
        ]
        return DashboardSummary(
            recentTasks=summaries,
            activeTasks=active,
            recentResults=recent_results,
        )

    def get_history(
        self,
        *,
        q: str | None = None,
        status: TaskStatus | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> HistoryList:
        tasks = [self._normalize_task_result_status(task) for task in self._task_repository.list_tasks()]
        if q is not None and q != "":
            tasks = [task for task in tasks if q in task.title]
        if status is not None:
            tasks = [task for task in tasks if task.status is status]
        start_index = 0
        if cursor:
            cursor_key = self._decode_cursor(cursor)
            start_index = self._resolve_cursor_index(tasks, cursor_key)
        page_items = tasks[start_index : start_index + limit]
        next_cursor = None
        if page_items and start_index + limit < len(tasks):
            next_cursor = self._encode_cursor(page_items[-1])
        return HistoryList(
            items=[self._to_summary(task) for task in page_items],
            meta=MetaData(nextCursor=next_cursor, limit=limit),
        )

    def _resolve_cursor_index(
        self,
        tasks: list[EvaluationTask],
        cursor_key: tuple[str, str],
    ) -> int:
        for index, task in enumerate(tasks):
            if (task.createdAt.isoformat(), task.taskId) == cursor_key:
                return index + 1
        raise ValueError("cursor 无效。")

    def _encode_cursor(self, task: EvaluationTask) -> str:
        raw_cursor = f"{task.createdAt.isoformat()}|{task.taskId}".encode("utf-8")
        return base64.urlsafe_b64encode(raw_cursor).decode("ascii")

    def _decode_cursor(self, cursor: str) -> tuple[str, str]:
        try:
            raw_value = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError("cursor 无效。") from exc
        created_at, separator, task_id = raw_value.partition("|")
        if not separator or not created_at or not task_id:
            raise ValueError("cursor 无效。")
        try:
            datetime.fromisoformat(created_at)
        except ValueError as exc:
            raise ValueError("cursor 无效。") from exc
        return created_at, task_id

    def _to_summary(self, task: EvaluationTask) -> EvaluationTaskSummary:
        return EvaluationTaskSummary(
            taskId=task.taskId,
            title=task.title,
            inputSummary=task.inputSummary,
            inputComposition=task.inputComposition,
            status=task.status,
            resultStatus=task.resultStatus,
            createdAt=task.createdAt,
        )

    def _normalize_task_result_status(self, task: EvaluationTask) -> EvaluationTask:
        if task.status is not TaskStatus.COMPLETED or task.resultStatus is not ResultStatus.AVAILABLE:
            return task
        result = self._task_repository.get_result(task.taskId)
        if result is not None and result.resultStatus is ResultStatus.AVAILABLE and result.result is not None:
            return task
        return task.model_copy(update={"resultStatus": ResultStatus.NOT_AVAILABLE})

    def _build_input_summary(self, request: JointSubmissionRequest) -> str:
        if request.hasChapters and request.hasOutline:
            return f"已提交 {len(request.chapters or [])} 章正文和 1 份大纲"
        if request.hasChapters:
            return f"仅提交 {len(request.chapters or [])} 章正文"
        return "仅提交大纲"

    def _build_input_screening(self, task_id: str, request: JointSubmissionRequest) -> InputScreeningResult:
        evaluation_mode = self._derive_evaluation_mode(request.inputComposition)
        runtime_metadata = self._resolve_runtime_metadata(
            stage=StageName.INPUT_SCREENING,
            input_composition=request.inputComposition,
            evaluation_mode=evaluation_mode,
        )
        return InputScreeningResult(
            taskId=task_id,
            schemaVersion=runtime_metadata.schema_version,
            promptVersion=runtime_metadata.prompt_version,
            rubricVersion=runtime_metadata.rubric_version,
            providerId=runtime_metadata.provider_id,
            modelId=runtime_metadata.model_id,
            inputComposition=request.inputComposition,
            hasChapters=request.hasChapters,
            hasOutline=request.hasOutline,
            chaptersSufficiency=self._derive_sufficiency(request.hasChapters),
            outlineSufficiency=self._derive_sufficiency(request.hasOutline),
            evaluationMode=evaluation_mode,
            rateable=True,
            status=StageStatus.OK,
            rejectionReasons=[],
            riskTags=[],
            segmentationPlan=None,
            confidence=0.95 if request.inputComposition is InputComposition.CHAPTERS_OUTLINE else 0.85,
            continueAllowed=True,
        )

    def _build_final_projection(
        self,
        task: EvaluationTask,
        *,
        signing_probability: int,
        commercial_value: int,
        writing_quality: int,
        innovation_score: int,
    ) -> FinalEvaluationProjection:
        runtime_metadata = self._resolve_projection_metadata(task)
        score_by_axis = {
            AxisId.HOOK_RETENTION: signing_probability,
            AxisId.SERIAL_MOMENTUM: commercial_value,
            AxisId.CHARACTER_DRIVE: writing_quality,
            AxisId.NARRATIVE_CONTROL: innovation_score,
            AxisId.PACING_PAYOFF: writing_quality,
            AxisId.SETTING_DIFFERENTIATION: innovation_score,
            AxisId.PLATFORM_FIT: signing_probability,
            AxisId.COMMERCIAL_POTENTIAL: commercial_value,
        }
        axes = [
            AxisEvaluationResult(
                axisId=axis_id,
                scoreBand=self._score_to_band(score_by_axis[axis_id]),
                score=score_by_axis[axis_id],
                summary=f"{axis_id.value} 维度总结",
                reason="当前阶段使用服务层 deterministic 投影占位。",
                degradedByInput=task.evaluationMode is EvaluationMode.DEGRADED,
                riskTags=[FatalRisk.INSUFFICIENT_MATERIAL] if task.evaluationMode is EvaluationMode.DEGRADED else [],
            )
            for axis_id in AxisId
        ]
        overall = OverallEvaluationResult(
            score=signing_probability,
            verdict="可继续观察",
            verdictSubQuote="当前样本已体现基础市场承接力，但仍需观察长线兑现稳定性。",
            summary="整体完成度稳定，仍需观察兑现强度。",
            platformCandidates=[
                PlatformCandidate(
                    name="女频平台 A",
                    weight=100,
                    pitchQuote="情感走向与平台核心读者预期一致，具备明确承接空间。",
                )
            ],
            marketFit="具备一定市场接受度",
            strengths=["结构完成度稳定"],
            weaknesses=["长线兑现仍需继续观察"],
        )
        return FinalEvaluationProjection(
            taskId=task.taskId,
            schemaVersion=runtime_metadata.schema_version,
            promptVersion=runtime_metadata.prompt_version,
            rubricVersion=runtime_metadata.rubric_version,
            providerId=runtime_metadata.provider_id,
            modelId=runtime_metadata.model_id,
            axes=axes,
            overall=overall,
        )

    def _build_result_from_projection(
        self,
        projection: FinalEvaluationProjection,
        *,
        result_time,
    ) -> EvaluationResult:
        return EvaluationResult(
            taskId=projection.taskId,
            schemaVersion=projection.schemaVersion,
            promptVersion=projection.promptVersion,
            rubricVersion=projection.rubricVersion,
            providerId=projection.providerId,
            modelId=projection.modelId,
            resultTime=result_time,
            axes=projection.axes,
            overall=projection.overall,
            typeAssessment=projection.typeAssessment,
        )

    def _resolve_runtime_metadata(
        self,
        *,
        stage: StageName,
        input_composition: InputComposition,
        evaluation_mode: EvaluationMode,
        provider_id: str | None = None,
        model_id: str | None = None,
    ) -> RuntimeMetadata:
        if self._prompt_runtime is None or self._provider_adapter is None:
            return RuntimeMetadata(
                schema_version="1.0.0",
                prompt_version="v1",
                rubric_version="rubric-v1",
                provider_id=provider_id or "provider-local",
                model_id=model_id or "model-local",
            )
        resolved_provider_id = provider_id or self._provider_adapter.provider_id
        resolved_model_id = model_id or self._provider_adapter.model_id
        resolved_prompt = self._prompt_runtime.resolve(
            stage=stage.value,
            input_composition=input_composition.value,
            evaluation_mode=evaluation_mode.value,
            provider_id=resolved_provider_id,
            model_id=resolved_model_id,
        )
        return RuntimeMetadata(
            schema_version=resolved_prompt.schemaVersion,
            prompt_version=resolved_prompt.promptVersion,
            rubric_version=resolved_prompt.rubricVersion,
            provider_id=resolved_provider_id,
            model_id=resolved_model_id,
        )

    def _resolve_projection_metadata(self, task: EvaluationTask) -> RuntimeMetadata:
        if all(
            value is not None
            for value in (
                task.schemaVersion,
                task.promptVersion,
                task.rubricVersion,
                task.providerId,
                task.modelId,
            )
        ):
            return RuntimeMetadata(
                schema_version=task.schemaVersion,
                prompt_version=task.promptVersion,
                rubric_version=task.rubricVersion,
                provider_id=task.providerId,
                model_id=task.modelId,
            )
        return self._resolve_runtime_metadata(
            stage=StageName.INPUT_SCREENING,
            input_composition=task.inputComposition,
            evaluation_mode=task.evaluationMode,
            provider_id=task.providerId,
            model_id=task.modelId,
        )

    def _derive_sufficiency(self, present: bool) -> Sufficiency:
        if present:
            return Sufficiency.SUFFICIENT
        return Sufficiency.MISSING

    def _derive_evaluation_mode(self, input_composition: InputComposition) -> EvaluationMode:
        if input_composition is InputComposition.CHAPTERS_OUTLINE:
            return EvaluationMode.FULL
        return EvaluationMode.DEGRADED

    def _score_to_band(self, score: int) -> ScoreBand:
        ordered_bands = [
            (90, ScoreBand.FOUR),
            (75, ScoreBand.THREE),
            (55, ScoreBand.TWO),
            (35, ScoreBand.ONE),
        ]
        for threshold, band in ordered_bands:
            if score >= threshold:
                return band
        return ScoreBand.ZERO
