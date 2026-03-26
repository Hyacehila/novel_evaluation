from __future__ import annotations

from typing import Literal

from pydantic import StrictBool

from packages.schemas.common.base import SchemaModel

PromptLifecycleStatus = Literal[
    "draft",
    "review",
    "candidate",
    "active",
    "deprecated",
    "retired",
]
PromptStage = Literal["input_screening", "rubric_evaluation", "aggregation"]


class PromptRegistryRecord(SchemaModel):
    promptId: str
    stage: PromptStage
    status: PromptLifecycleStatus
    schemaVersion: str
    rubricVersion: str
    inputCompositionScope: str
    evaluationModeScope: str
    providerScope: str
    modelScope: str
    enabled: StrictBool
    notes: str | None = None


class PromptVersionRecord(SchemaModel):
    promptId: str
    promptVersion: str
    status: PromptLifecycleStatus
    schemaVersion: str
    rubricVersion: str
    owner: str
    updatedAt: str
    changeSummary: str
    rollbackTarget: str
    evalRequirement: str


class ResolvedPrompt(SchemaModel):
    promptId: str
    promptVersion: str
    body: str
    schemaVersion: str
    rubricVersion: str
