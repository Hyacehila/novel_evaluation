from __future__ import annotations

import logging

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import AggregationExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.application.support.process_logging import log_event
from packages.schemas.common.enums import StageName
from packages.schemas.output.error import ErrorCode
from packages.schemas.stages.aggregation import AggregatedRubricResult

logger = logging.getLogger(__name__)


def execute_aggregation(
    *,
    provider_adapter: ProviderExecutionPort,
    context: AggregationExecutionContext,
) -> AggregatedRubricResult:
    payload = execute_provider_stage(
        provider_adapter=provider_adapter,
        binding=context.binding,
        task_id=context.task_id,
        stage=StageName.AGGREGATION,
        input_composition=context.screening.inputComposition,
        evaluation_mode=context.screening.evaluationMode,
        response_format={"type": "json_object"},
        user_payload={
            "taskId": context.task_id,
            "title": context.submission.title,
            "chapters": [chapter.content for chapter in context.submission.chapters or []],
            "outline": context.submission.outline.content if context.submission.outline is not None else None,
            "screening": context.screening.model_dump(mode="json"),
            "rubric": context.rubric.model_dump(mode="json"),
            "consistency": context.consistency.model_dump(mode="json"),
        },
    )
    try:
        return AggregatedRubricResult.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        log_event(
            logger,
            logging.ERROR,
            "stage_schema_invalid",
            taskId=context.task_id,
            stage=StageName.AGGREGATION,
            promptVersion=context.binding.prompt_version,
            schemaVersion=context.binding.schema_version,
            rubricVersion=context.binding.rubric_version,
            providerId=context.binding.provider_id,
            modelId=context.binding.model_id,
            errorCode=ErrorCode.STAGE_SCHEMA_INVALID,
            durationMs=0,
        )
        raise PipelineFailureError(
            error_code=ErrorCode.STAGE_SCHEMA_INVALID,
            message="aggregation 阶段输出不满足正式 schema。",
        ) from exc
