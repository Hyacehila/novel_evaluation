from __future__ import annotations

from packages.schemas.common.base import SchemaModel


class PromptRegistryRecord(SchemaModel):
    promptId: str
    stage: str
    status: str
    schemaVersion: str
    rubricVersion: str
    inputCompositionScope: str
    evaluationModeScope: str
    providerScope: str
    modelScope: str
    enabled: bool
    notes: str | None = None


class PromptVersionRecord(SchemaModel):
    promptId: str
    promptVersion: str
    status: str
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
