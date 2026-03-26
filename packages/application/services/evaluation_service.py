from __future__ import annotations

from packages.application.ports.runtime_metadata import (
    PromptRuntimePort,
    ProviderMetadataPort,
    RuntimeMetadata,
    StaticPromptRuntime,
    StaticProviderMetadata,
)
from packages.application.ports.task_repository import TaskRepository
from packages.application.support.clock import Clock, UtcClock
from packages.application.support.id_generator import IdGenerator, UuidTaskIdGenerator
from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    InputComposition,
    ResultStatus,
    SkeletonDimensionId,
    StageName,
    StageStatus,
    Sufficiency,
    TaskStatus,
    TopLevelScoreField,
)
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.dashboard import DashboardSummary, HistoryList
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.result import (
    DetailedAnalysis,
    EvaluationResult,
    EvaluationResultResource,
    FinalEvaluationProjection,
    PlatformRecommendation,
)
from packages.schemas.output.task import EvaluationTask, EvaluationTaskSummary, RecentResultSummary


class EvaluationService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        prompt_runtime: PromptRuntimePort | None = None,
        provider_adapter: ProviderMetadataPort | None = None,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._task_repository = task_repository
        self._prompt_runtime = prompt_runtime or StaticPromptRuntime()
        self._provider_adapter = provider_adapter or StaticProviderMetadata()
        self._id_generator = id_generator or UuidTaskIdGenerator()
        self._clock = clock or UtcClock()

    def create_task(self, request: JointSubmissionRequest) -> EvaluationTask:
        task_id = self._id_generator.new_task_id()
        screening = self._build_input_screening(task_id, request)
        now = self._clock.now()
        task = EvaluationTask(
            taskId=task_id,
            title=request.title,
            inputSummary=self._build_input_summary(request),
            inputComposition=screening.inputComposition,
            hasChapters=screening.hasChapters,
            hasOutline=screening.hasOutline,
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
        return self._task_repository.create_task(task)

    def get_task(self, task_id: str) -> EvaluationTask:
        task = self._task_repository.get_task(task_id)
        if task is None:
            raise LookupError("任务不存在。")
        return task

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

    def get_dashboard(self) -> DashboardSummary:
        tasks = self._task_repository.list_tasks()
        summaries = [self._to_summary(task) for task in tasks]
        active = [summary for task, summary in zip(tasks, summaries) if task.status is TaskStatus.PROCESSING]
        recent_results = [
            RecentResultSummary(
                taskId=task.taskId,
                title=task.title,
                resultTime=result.resultTime,
                signingProbability=result.result.signingProbability,
                editorVerdict=result.result.editorVerdict,
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

    def get_history(self) -> HistoryList:
        limit = 20
        tasks = self._task_repository.list_tasks()
        recent_tasks = tasks[-limit:]
        return HistoryList(
            items=[self._to_summary(task) for task in recent_tasks],
            meta={"nextCursor": None, "limit": limit},
        )

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
        return FinalEvaluationProjection(
            taskId=task.taskId,
            schemaVersion=runtime_metadata.schema_version,
            promptVersion=runtime_metadata.prompt_version,
            rubricVersion=runtime_metadata.rubric_version,
            providerId=runtime_metadata.provider_id,
            modelId=runtime_metadata.model_id,
            signingProbability=signing_probability,
            commercialValue=commercial_value,
            writingQuality=writing_quality,
            innovationScore=innovation_score,
            strengths=["题材明确"],
            weaknesses=["开篇冲突偏弱"],
            platforms=[PlatformRecommendation(name="女频平台 A", percentage=82, reason="题材匹配度较高")],
            marketFit="具备一定市场接受度",
            editorVerdict="可继续观察",
            detailedAnalysis=DetailedAnalysis(
                plot="情节推进稳定",
                character="角色动机明确",
                pacing="节奏略慢",
                worldBuilding="设定表达完整",
            ),
            overallConfidence=0.82,
            supportingAxisMap=self._build_supporting_axis_map(),
            supportingSkeletonMap=self._build_supporting_skeleton_map(),
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
            signingProbability=projection.signingProbability,
            commercialValue=projection.commercialValue,
            writingQuality=projection.writingQuality,
            innovationScore=projection.innovationScore,
            strengths=projection.strengths,
            weaknesses=projection.weaknesses,
            platforms=projection.platforms,
            marketFit=projection.marketFit,
            editorVerdict=projection.editorVerdict,
            detailedAnalysis=projection.detailedAnalysis,
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

    def _build_supporting_axis_map(self) -> dict[TopLevelScoreField, list[AxisId]]:
        return {
            TopLevelScoreField.SIGNING_PROBABILITY: [AxisId.COMMERCIAL_POTENTIAL, AxisId.PLATFORM_FIT],
            TopLevelScoreField.COMMERCIAL_VALUE: [AxisId.COMMERCIAL_POTENTIAL, AxisId.SERIAL_MOMENTUM],
            TopLevelScoreField.WRITING_QUALITY: [AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF],
            TopLevelScoreField.INNOVATION_SCORE: [AxisId.SETTING_DIFFERENTIATION, AxisId.HOOK_RETENTION],
        }

    def _build_supporting_skeleton_map(self) -> dict[TopLevelScoreField, list[SkeletonDimensionId]]:
        return {
            TopLevelScoreField.SIGNING_PROBABILITY: [SkeletonDimensionId.MARKET_ATTRACTION],
            TopLevelScoreField.COMMERCIAL_VALUE: [SkeletonDimensionId.MARKET_ATTRACTION, SkeletonDimensionId.NOVELTY_UTILITY],
            TopLevelScoreField.WRITING_QUALITY: [SkeletonDimensionId.NARRATIVE_EXECUTION],
            TopLevelScoreField.INNOVATION_SCORE: [SkeletonDimensionId.NOVELTY_UTILITY, SkeletonDimensionId.CHARACTER_MOMENTUM],
        }
