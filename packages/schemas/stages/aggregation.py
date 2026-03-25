from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import AxisId, FatalRisk, SkeletonDimensionId, StageName, TopLevelScoreField
from packages.schemas.common.validators import ensure_non_empty_text, validate_confidence, validate_percentage
from packages.schemas.output.result import DetailedAnalysis


class AggregatedRubricResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.AGGREGATION] = StageName.AGGREGATION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    axisScores: dict[AxisId, int]
    skeletonScores: dict[SkeletonDimensionId, int]
    topLevelScoresDraft: dict[TopLevelScoreField, int]
    strengthCandidates: list[str]
    weaknessCandidates: list[str]
    platformCandidates: list[str]
    marketFitDraft: str
    editorVerdictDraft: str
    detailedAnalysisDraft: DetailedAnalysis
    supportingAxisMap: dict[TopLevelScoreField, list[AxisId]]
    supportingSkeletonMap: dict[TopLevelScoreField, list[SkeletonDimensionId]]
    riskTags: list[FatalRisk]
    overallConfidence: float

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
        "marketFitDraft",
        "editorVerdictDraft",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "aggregation field")

    @field_validator("strengthCandidates", "weaknessCandidates", "platformCandidates")
    @classmethod
    def validate_text_lists(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "candidate item") for item in value]

    @field_validator("overallConfidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "overallConfidence")

    @field_validator("axisScores", "skeletonScores", "topLevelScoresDraft")
    @classmethod
    def validate_score_maps(cls, value: dict[object, int]) -> dict[object, int]:
        return {key: validate_percentage(score, "score") for key, score in value.items()}

    @field_validator("supportingAxisMap", "supportingSkeletonMap")
    @classmethod
    def validate_supporting_maps(cls, value: dict[object, list[object]]) -> dict[object, list[object]]:
        if not value:
            raise ValueError("supporting map 不能为空。")
        return value

    @model_validator(mode="after")
    def validate_fixed_maps(self) -> "AggregatedRubricResult":
        if set(self.axisScores.keys()) != set(AxisId):
            raise ValueError("axisScores 必须覆盖全部 8 轴。")
        if set(self.skeletonScores.keys()) != set(SkeletonDimensionId):
            raise ValueError("skeletonScores 必须覆盖全部骨架维度。")
        if set(self.topLevelScoresDraft.keys()) != set(TopLevelScoreField):
            raise ValueError("topLevelScoresDraft 必须覆盖全部顶层分数字段。")
        if set(self.supportingAxisMap.keys()) != set(TopLevelScoreField):
            raise ValueError("supportingAxisMap 必须覆盖全部顶层分数字段。")
        if set(self.supportingSkeletonMap.keys()) != set(TopLevelScoreField):
            raise ValueError("supportingSkeletonMap 必须覆盖全部顶层分数字段。")
        return self
