from __future__ import annotations

from packages.application.scoring_pipeline.models import RubricExecutionContext
from packages.schemas.common.enums import AxisId, EvaluationMode, InputComposition
from packages.schemas.stages.consistency import (
    ConflictSeverity,
    ConflictType,
    ConsistencyCheckResult,
    ConsistencyConflict,
)


_GENRE_KEYWORDS = {
    "urban": ("都市", "总裁", "豪门", "职场"),
    "scifi": ("星际", "机甲", "宇宙", "赛博"),
    "fantasy": ("修仙", "宗门", "仙门", "灵气"),
    "horror": ("规则怪谈", "诡异", "惊悚"),
    "romance": ("恋爱", "婚约", "感情"),
}


def run_consistency_check(*, context: RubricExecutionContext, rubric) -> ConsistencyCheckResult:
    chapters_text = "\n".join(chapter.content for chapter in context.submission.chapters or [])
    outline_text = context.submission.outline.content if context.submission.outline is not None else ""
    conflicts: list[ConsistencyConflict] = []
    normalization_notes: list[str] = []
    cross_input_mismatch_detected = False

    if context.screening.evaluationMode is EvaluationMode.DEGRADED:
        normalization_notes.append("当前输入以 degraded 模式执行，部分长线判断置信度已下调。")

    chapter_genre = _infer_genre(chapters_text)
    outline_genre = _infer_genre(outline_text)
    if (
        context.screening.inputComposition is InputComposition.CHAPTERS_OUTLINE
        and chapter_genre is not None
        and outline_genre is not None
        and chapter_genre != outline_genre
    ):
        cross_input_mismatch_detected = True
        conflicts.append(
            ConsistencyConflict(
                conflictId="conflict_cross_input_mismatch",
                conflictType=ConflictType.CROSS_INPUT_MISMATCH,
                relatedEvaluationIds=[item.evaluationId for item in rubric.items[:2]],
                description="正文与大纲的核心题材信号不一致，存在跨输入承诺冲突。",
                severity=ConflictSeverity.HIGH,
                normalizationNote="需人工复核投稿包是否混入了不同作品或大纲漂移。",
            )
        )
        normalization_notes.append("检测到正文与大纲题材冲突，主链在 consistency_check 终止。")

    weak_evidence_items = [item for item in rubric.items if item.confidence < 0.3]
    if weak_evidence_items:
        conflicts.append(
            ConsistencyConflict(
                conflictId="conflict_weak_evidence",
                conflictType=ConflictType.WEAK_EVIDENCE,
                relatedEvaluationIds=[item.evaluationId for item in weak_evidence_items[:4]],
                description="部分 rubric 评价项置信度较低，需要在聚合前提示弱证据风险。",
                severity=ConflictSeverity.MEDIUM,
                normalizationNote="弱证据项不会直接阻断，但会压低整体置信度。",
            )
        )
        normalization_notes.append("存在弱证据项，聚合阶段将降低整体置信度。")

    missing_required_axes = list(rubric.missingRequiredAxes)
    passed = not cross_input_mismatch_detected and not missing_required_axes
    continue_allowed = passed
    confidence = 0.36 if cross_input_mismatch_detected else (0.72 if weak_evidence_items else 0.84)

    return ConsistencyCheckResult(
        taskId=context.task_id,
        schemaVersion=context.binding.schema_version,
        promptVersion=context.binding.prompt_version,
        rubricVersion=context.binding.rubric_version,
        providerId=context.binding.provider_id,
        modelId=context.binding.model_id,
        inputComposition=context.screening.inputComposition,
        evaluationMode=context.screening.evaluationMode,
        passed=passed,
        conflicts=conflicts,
        crossInputMismatchDetected=cross_input_mismatch_detected,
        unsupportedClaimsDetected=False,
        duplicatedPenaltiesDetected=False,
        missingRequiredAxes=missing_required_axes,
        normalizationNotes=normalization_notes,
        confidence=confidence,
        continueAllowed=continue_allowed,
    )


def _infer_genre(text: str) -> str | None:
    normalized = text.strip()
    if not normalized:
        return None
    for genre, keywords in _GENRE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return genre
    return None
