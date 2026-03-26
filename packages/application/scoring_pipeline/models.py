from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from packages.schemas.common.enums import EvaluationMode, StageName
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.result import FinalEvaluationProjection
from packages.schemas.stages.aggregation import AggregatedRubricResult
from packages.schemas.stages.consistency import ConsistencyCheckResult
from packages.schemas.stages.rubric import RubricEvaluationSet


@dataclass(frozen=True, slots=True)
class StagePromptBinding:
    stage: StageName
    prompt_id: str
    prompt_version: str
    schema_version: str
    rubric_version: str
    provider_id: str
    model_id: str
    prompt_body: str

    @property
    def request_id(self) -> str:
        return f"{self.stage.value}_{uuid4().hex}"


@dataclass(frozen=True, slots=True)
class ScreeningExecutionContext:
    task_id: str
    submission: JointSubmissionRequest
    input_composition: str
    evaluation_mode_hint: EvaluationMode
    binding: StagePromptBinding


@dataclass(frozen=True, slots=True)
class RubricExecutionContext:
    task_id: str
    submission: JointSubmissionRequest
    screening: InputScreeningResult
    binding: StagePromptBinding


@dataclass(frozen=True, slots=True)
class AggregationExecutionContext:
    task_id: str
    submission: JointSubmissionRequest
    screening: InputScreeningResult
    rubric: RubricEvaluationSet
    consistency: ConsistencyCheckResult
    binding: StagePromptBinding


@dataclass(frozen=True, slots=True)
class ScoringPipelineResult:
    screening: InputScreeningResult
    rubric: RubricEvaluationSet
    consistency: ConsistencyCheckResult
    aggregation: AggregatedRubricResult
    projection: FinalEvaluationProjection
