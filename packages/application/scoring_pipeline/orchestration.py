from __future__ import annotations

import logging
from time import perf_counter

from packages.application.ports.runtime_metadata import PromptRuntimePort, ProviderExecutionPort
from packages.application.scoring_pipeline.aggregation_executor import execute_aggregation
from packages.application.scoring_pipeline.consistency_service import run_consistency_check
from packages.application.scoring_pipeline.exceptions import PipelineBlockedError
from packages.application.scoring_pipeline.models import (
    AggregationExecutionContext,
    RubricExecutionContext,
    ScoringPipelineResult,
    ScreeningExecutionContext,
    StagePromptBinding,
    TypeClassificationExecutionContext,
    TypeLensExecutionContext,
)
from packages.application.scoring_pipeline.projection_service import build_final_projection
from packages.application.scoring_pipeline.rubric_executor import RUBRIC_SLICE_PLAN, execute_rubric
from packages.application.scoring_pipeline.screening_executor import execute_screening
from packages.application.scoring_pipeline.type_classification_executor import execute_type_classification
from packages.application.scoring_pipeline.type_lens_executor import execute_type_lens
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.common.enums import EvaluationMode, InputComposition, StageName, Sufficiency
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.task import EvaluationTask
from packages.schemas.stages.type_classification import TypeClassificationResult
from packages.runtime.logging import log_event

logger = logging.getLogger(__name__)


class ScoringPipeline:
    def __init__(
        self,
        *,
        prompt_runtime: PromptRuntimePort,
        provider_adapter: ProviderExecutionPort,
    ) -> None:
        self._prompt_runtime = prompt_runtime
        self._provider_adapter = provider_adapter

    def run(self, *, task: EvaluationTask, submission: JointSubmissionRequest) -> ScoringPipelineResult:
        screening = self.run_screening(task=task, submission=submission)
        type_classification = self.run_type_classification(
            task=task,
            submission=submission,
            screening=screening,
        )
        return self.run_after_type_classification(
            task=task,
            submission=submission,
            screening=screening,
            type_classification=type_classification,
        )

    def run_screening(self, *, task: EvaluationTask, submission: JointSubmissionRequest) -> InputScreeningResult:
        input_composition = submission.inputComposition.value
        evaluation_mode_hint = (
            EvaluationMode.FULL if submission.inputComposition is InputComposition.CHAPTERS_OUTLINE else EvaluationMode.DEGRADED
        )
        screening_binding = self._resolve_binding(
            stage=StageName.INPUT_SCREENING,
            input_composition=input_composition,
            evaluation_mode=evaluation_mode_hint.value,
        )
        screening = execute_screening(
            provider_adapter=self._provider_adapter,
            context=ScreeningExecutionContext(
                task_id=task.taskId,
                submission=submission,
                input_composition=input_composition,
                evaluation_mode_hint=evaluation_mode_hint,
                binding=screening_binding,
            ),
        )
        return screening

    def run_after_screening(
        self,
        *,
        task: EvaluationTask,
        submission: JointSubmissionRequest,
        screening: InputScreeningResult,
    ) -> ScoringPipelineResult:
        type_classification = self.run_type_classification(
            task=task,
            submission=submission,
            screening=screening,
        )
        return self.run_after_type_classification(
            task=task,
            submission=submission,
            screening=screening,
            type_classification=type_classification,
        )

    def run_type_classification(
        self,
        *,
        task: EvaluationTask,
        submission: JointSubmissionRequest,
        screening: InputScreeningResult,
    ) -> TypeClassificationResult:
        self._ensure_screening_continue_allowed(task_id=task.taskId, screening=screening)
        type_classification_binding = self._resolve_binding(
            stage=StageName.TYPE_CLASSIFICATION,
            input_composition=screening.inputComposition.value,
            evaluation_mode=screening.evaluationMode.value,
        )
        return execute_type_classification(
            provider_adapter=self._provider_adapter,
            context=TypeClassificationExecutionContext(
                task_id=task.taskId,
                submission=submission,
                screening=screening,
                binding=type_classification_binding,
            ),
        )

    def run_after_type_classification(
        self,
        *,
        task: EvaluationTask,
        submission: JointSubmissionRequest,
        screening: InputScreeningResult,
        type_classification: TypeClassificationResult,
    ) -> ScoringPipelineResult:
        rubric_binding = self._resolve_binding(
            stage=StageName.RUBRIC_EVALUATION,
            input_composition=screening.inputComposition.value,
            evaluation_mode=screening.evaluationMode.value,
        )
        rubric_context = RubricExecutionContext(
            task_id=task.taskId,
            submission=submission,
            screening=screening,
            binding=rubric_binding,
        )
        rubric = execute_rubric(provider_adapter=self._provider_adapter, context=rubric_context)
        type_lens_binding = self._resolve_binding(
            stage=StageName.TYPE_LENS_EVALUATION,
            input_composition=screening.inputComposition.value,
            evaluation_mode=screening.evaluationMode.value,
        )
        type_lens = execute_type_lens(
            provider_adapter=self._provider_adapter,
            context=TypeLensExecutionContext(
                task_id=task.taskId,
                submission=submission,
                screening=screening,
                type_classification=type_classification,
                binding=type_lens_binding,
            ),
        )
        consistency_started_at = perf_counter()
        consistency = run_consistency_check(context=rubric_context, rubric=rubric)
        consistency_duration_ms = int((perf_counter() - consistency_started_at) * 1000)
        log_event(
            logger,
            logging.INFO,
            "stage_completed",
            taskId=task.taskId,
            stage=StageName.CONSISTENCY_CHECK,
            promptVersion=consistency.promptVersion,
            schemaVersion=consistency.schemaVersion,
            rubricVersion=consistency.rubricVersion,
            providerId=consistency.providerId,
            modelId=consistency.modelId,
            durationMs=consistency_duration_ms,
        )
        if not consistency.continueAllowed:
            error_code = ErrorCode.JOINT_INPUT_MISMATCH if consistency.crossInputMismatchDetected else ErrorCode.RESULT_BLOCKED
            log_event(
                logger,
                logging.WARNING,
                "stage_blocked",
                taskId=task.taskId,
                stage=StageName.CONSISTENCY_CHECK,
                promptVersion=consistency.promptVersion,
                schemaVersion=consistency.schemaVersion,
                rubricVersion=consistency.rubricVersion,
                providerId=consistency.providerId,
                modelId=consistency.modelId,
                errorCode=error_code,
                durationMs=consistency_duration_ms,
            )
            raise PipelineBlockedError(
                error_code=error_code,
                message=_build_consistency_block_message(consistency),
            )

        aggregation_binding = self._resolve_binding(
            stage=StageName.AGGREGATION,
            input_composition=screening.inputComposition.value,
            evaluation_mode=screening.evaluationMode.value,
        )
        aggregation = execute_aggregation(
            provider_adapter=self._provider_adapter,
            context=AggregationExecutionContext(
                task_id=task.taskId,
                submission=submission,
                screening=screening,
                type_classification=type_classification,
                rubric=rubric,
                type_lens=type_lens,
                consistency=consistency,
                binding=aggregation_binding,
            ),
        )
        projection_started_at = perf_counter()
        projection = build_final_projection(
            aggregation=aggregation,
            type_classification=type_classification,
            rubric=rubric,
            type_lens=type_lens,
            consistency=consistency,
        )
        log_event(
            logger,
            logging.INFO,
            "stage_completed",
            taskId=task.taskId,
            stage=StageName.FINAL_PROJECTION,
            promptVersion=projection.promptVersion,
            schemaVersion=projection.schemaVersion,
            rubricVersion=projection.rubricVersion,
            providerId=projection.providerId,
            modelId=projection.modelId,
            durationMs=int((perf_counter() - projection_started_at) * 1000),
        )
        return ScoringPipelineResult(
            screening=screening,
            typeClassification=type_classification,
            rubric=rubric,
            typeLens=type_lens,
            consistency=consistency,
            aggregation=aggregation,
            projection=projection,
        )

    def _ensure_screening_continue_allowed(self, *, task_id: str, screening: InputScreeningResult) -> None:
        if screening.continueAllowed:
            return

        error_code = _map_screening_block_error(screening)
        log_event(
            logger,
            logging.WARNING,
            "stage_blocked",
            taskId=task_id,
            stage=StageName.INPUT_SCREENING,
            promptVersion=screening.promptVersion,
            schemaVersion=screening.schemaVersion,
            rubricVersion=screening.rubricVersion,
            providerId=screening.providerId,
            modelId=screening.modelId,
            errorCode=error_code,
            durationMs=0,
        )
        raise PipelineBlockedError(
            error_code=error_code,
            message=_build_screening_block_message(error_code=error_code),
        )

    def _resolve_binding(
        self,
        *,
        stage: StageName,
        input_composition: str,
        evaluation_mode: str,
    ) -> StagePromptBinding:
        resolved_prompt = self._prompt_runtime.resolve(
            stage=stage.value,
            input_composition=input_composition,
            evaluation_mode=evaluation_mode,
            provider_id=self._provider_adapter.provider_id,
            model_id=self._provider_adapter.model_id,
        )
        return StagePromptBinding(
            stage=stage,
            prompt_id=resolved_prompt.promptId,
            prompt_version=resolved_prompt.promptVersion,
            schema_version=resolved_prompt.schemaVersion,
            rubric_version=resolved_prompt.rubricVersion,
            provider_id=self._provider_adapter.provider_id,
            model_id=self._provider_adapter.model_id,
            prompt_body=resolved_prompt.body,
        )


def _map_screening_block_error(screening) -> ErrorCode:
    if screening.hasChapters and screening.chaptersSufficiency in {Sufficiency.INSUFFICIENT, Sufficiency.MISSING}:
        return ErrorCode.INSUFFICIENT_CHAPTERS_INPUT
    if screening.hasOutline and screening.outlineSufficiency in {Sufficiency.INSUFFICIENT, Sufficiency.MISSING}:
        return ErrorCode.INSUFFICIENT_OUTLINE_INPUT
    return ErrorCode.JOINT_INPUT_UNRATEABLE


def _build_screening_block_message(*, error_code: ErrorCode) -> str:
    if error_code is ErrorCode.INSUFFICIENT_CHAPTERS_INPUT:
        return "正文内容不足，当前无法进入正式评分，请补充正文后重试。"
    if error_code is ErrorCode.INSUFFICIENT_OUTLINE_INPUT:
        return "大纲内容不足，当前无法进入正式评分，请补充大纲后重试。"
    if error_code is ErrorCode.JOINT_INPUT_UNRATEABLE:
        return "输入材料未满足正式评分条件，当前无法进入正式评分，请补充材料后重试。"
    return "输入未满足正式评分的最小可评条件。"


def _build_consistency_block_message(consistency) -> str:
    if consistency.crossInputMismatchDetected:
        return "正文与大纲之间存在高严重度冲突，当前结果被阻断。"
    if consistency.missingRequiredAxes:
        joined_axes = ", ".join(axis.value for axis in consistency.missingRequiredAxes)
        return f"缺少必需评价轴，当前结果被阻断：{joined_axes}。"
    if consistency.unsupportedClaimsDetected:
        return "存在无依据结论，当前结果被阻断。"
    return "一致性整理未通过，当前结果被阻断。"
