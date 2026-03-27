from __future__ import annotations

from packages.application.scoring_pipeline.consistency_rules import (
    CONSISTENCY_CONFIDENCE_PROFILE,
    CONSISTENCY_KEYWORDS,
    CONSISTENCY_THRESHOLDS,
)
from packages.application.scoring_pipeline.models import RubricExecutionContext
from packages.schemas.common.enums import AxisId, EvaluationMode, FatalRisk, InputComposition
from packages.schemas.stages.consistency import (
    ConflictSeverity,
    ConflictType,
    ConsistencyCheckResult,
    ConsistencyConflict,
)


def run_consistency_check(*, context: RubricExecutionContext, rubric) -> ConsistencyCheckResult:
    chapters_text = "\n".join(chapter.content for chapter in context.submission.chapters or [])
    outline_text = context.submission.outline.content if context.submission.outline is not None else ""
    conflicts: list[ConsistencyConflict] = []
    normalization_notes: list[str] = []

    if context.screening.evaluationMode is EvaluationMode.DEGRADED:
        normalization_notes.append("当前输入以 degraded 模式执行，部分长线判断置信度已下调。")

    cross_input_conflict = _build_cross_input_conflict(
        chapters_text=chapters_text,
        outline_text=outline_text,
        input_composition=context.screening.inputComposition,
        evaluation_ids=[item.evaluationId for item in rubric.items],
    )
    if cross_input_conflict is not None:
        conflicts.append(cross_input_conflict)
        normalization_notes.append("检测到正文与大纲题材冲突，主链在 consistency_check 终止。")

    weak_evidence_conflict = _build_weak_evidence_conflict(rubric.items)
    if weak_evidence_conflict is not None:
        conflicts.append(weak_evidence_conflict)
        normalization_notes.append("存在弱证据项，聚合阶段将降低整体置信度。")

    unsupported_claim_conflict = _build_unsupported_claim_conflict(rubric.items)
    if unsupported_claim_conflict is not None:
        conflicts.append(unsupported_claim_conflict)
        normalization_notes.append("检测到结论强度高于证据强度的评价项，当前结果被阻断。")

    duplicated_penalty_conflict = _build_duplicated_penalty_conflict(rubric.items)
    if duplicated_penalty_conflict is not None:
        conflicts.append(duplicated_penalty_conflict)
        normalization_notes.append("检测到相同风险被重复处罚，聚合阶段需去重处理。")

    missing_required_axes = list(rubric.missingRequiredAxes)
    if missing_required_axes:
        conflicts.append(_build_missing_required_axes_conflict(missing_required_axes=missing_required_axes))
        normalization_notes.append(
            f"缺少必需评价轴：{', '.join(axis.value for axis in missing_required_axes)}，当前结果被阻断。"
        )

    cross_input_mismatch_detected = cross_input_conflict is not None
    unsupported_claims_detected = unsupported_claim_conflict is not None
    duplicated_penalties_detected = duplicated_penalty_conflict is not None
    passed = not cross_input_mismatch_detected and not unsupported_claims_detected and not missing_required_axes
    continue_allowed = passed
    confidence = _resolve_confidence(
        cross_input_mismatch_detected=cross_input_mismatch_detected,
        unsupported_claims_detected=unsupported_claims_detected,
        missing_required_axes=missing_required_axes,
        duplicated_penalties_detected=duplicated_penalties_detected,
        has_weak_evidence=weak_evidence_conflict is not None,
    )

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
        unsupportedClaimsDetected=unsupported_claims_detected,
        duplicatedPenaltiesDetected=duplicated_penalties_detected,
        missingRequiredAxes=missing_required_axes,
        normalizationNotes=normalization_notes,
        confidence=confidence,
        continueAllowed=continue_allowed,
    )


def _build_cross_input_conflict(
    *,
    chapters_text: str,
    outline_text: str,
    input_composition: InputComposition,
    evaluation_ids: list[str],
) -> ConsistencyConflict | None:
    chapter_genre = _infer_genre(chapters_text)
    outline_genre = _infer_genre(outline_text)
    if (
        input_composition is not InputComposition.CHAPTERS_OUTLINE
        or chapter_genre is None
        or outline_genre is None
        or chapter_genre == outline_genre
    ):
        return None
    return ConsistencyConflict(
        conflictId="conflict_cross_input_mismatch",
        conflictType=ConflictType.CROSS_INPUT_MISMATCH,
        relatedEvaluationIds=evaluation_ids[:2],
        description="正文与大纲的核心题材信号不一致，存在跨输入承诺冲突。",
        severity=ConflictSeverity.HIGH,
        normalizationNote="需人工复核投稿包是否混入了不同作品或大纲漂移。",
    )


def _build_weak_evidence_conflict(items) -> ConsistencyConflict | None:
    weak_evidence_items = [item for item in items if item.confidence < CONSISTENCY_THRESHOLDS.weak_evidence_confidence]
    if not weak_evidence_items:
        return None
    return ConsistencyConflict(
        conflictId="conflict_weak_evidence",
        conflictType=ConflictType.WEAK_EVIDENCE,
        relatedEvaluationIds=[item.evaluationId for item in weak_evidence_items[: CONSISTENCY_THRESHOLDS.max_related_evaluation_ids]],
        description="部分 rubric 评价项置信度较低，需要在聚合前提示弱证据风险。",
        severity=ConflictSeverity.MEDIUM,
        normalizationNote="弱证据项不会直接阻断，但会压低整体置信度。",
    )


def _build_unsupported_claim_conflict(items) -> ConsistencyConflict | None:
    unsupported_items = [
        item
        for item in items
        if _is_unsupported_claim(item)
    ]
    if not unsupported_items:
        return None
    return ConsistencyConflict(
        conflictId="conflict_unsupported_claim",
        conflictType=ConflictType.UNSUPPORTED_CLAIM,
        relatedEvaluationIds=[item.evaluationId for item in unsupported_items[: CONSISTENCY_THRESHOLDS.max_related_evaluation_ids]],
        description="部分评价项结论强度高于证据强度，存在无依据结论风险。",
        severity=ConflictSeverity.HIGH,
        normalizationNote="无依据结论会直接阻断正式结果，需回退到更保守的判断。",
    )


def _build_duplicated_penalty_conflict(items) -> ConsistencyConflict | None:
    duplicate_related_ids: list[str] = []
    stale_formula_hits = 0
    for item in items:
        has_duplicate_signal = FatalRisk.STALE_FORMULA in item.riskTags or any(
            "重复处罚" in signal for signal in item.blockingSignals
        )
        if has_duplicate_signal:
            stale_formula_hits += 1
            duplicate_related_ids.append(item.evaluationId)
    if stale_formula_hits < CONSISTENCY_THRESHOLDS.duplicated_penalty_occurrences:
        return None
    return ConsistencyConflict(
        conflictId="conflict_duplicated_penalty",
        conflictType=ConflictType.DUPLICATED_PENALTY,
        relatedEvaluationIds=duplicate_related_ids[: CONSISTENCY_THRESHOLDS.max_related_evaluation_ids],
        description="相同风险在多个评价项上被重复处罚，存在聚合重复扣分风险。",
        severity=ConflictSeverity.MEDIUM,
        normalizationNote="重复处罚需要在聚合时去重，避免单一问题被多次放大。",
    )


def _build_missing_required_axes_conflict(*, missing_required_axes: list[AxisId]) -> ConsistencyConflict:
    return ConsistencyConflict(
        conflictId="conflict_missing_required_axis",
        conflictType=ConflictType.MISSING_REQUIRED_AXIS,
        relatedEvaluationIds=[],
        description=f"缺少必需评价轴：{', '.join(axis.value for axis in missing_required_axes)}。",
        severity=ConflictSeverity.HIGH,
        normalizationNote="缺轴会导致正式投影失真，当前结果不能继续下游聚合。",
    )


def _resolve_confidence(
    *,
    cross_input_mismatch_detected: bool,
    unsupported_claims_detected: bool,
    missing_required_axes: list[AxisId],
    duplicated_penalties_detected: bool,
    has_weak_evidence: bool,
) -> float:
    if cross_input_mismatch_detected:
        return CONSISTENCY_CONFIDENCE_PROFILE.cross_input_mismatch
    if unsupported_claims_detected:
        return CONSISTENCY_CONFIDENCE_PROFILE.unsupported_claim
    if missing_required_axes:
        return CONSISTENCY_CONFIDENCE_PROFILE.missing_required_axes
    if duplicated_penalties_detected:
        return CONSISTENCY_CONFIDENCE_PROFILE.duplicated_penalty
    if has_weak_evidence:
        return CONSISTENCY_CONFIDENCE_PROFILE.weak_evidence_only
    return CONSISTENCY_CONFIDENCE_PROFILE.clean


def _is_unsupported_claim(item) -> bool:
    reason = item.reason.strip()
    if not reason or not any(token in reason for token in CONSISTENCY_KEYWORDS.assertive_reason_tokens):
        return False
    if not item.evidenceRefs:
        return True
    return all(
        evidence.confidence < CONSISTENCY_THRESHOLDS.unsupported_claim_evidence_confidence
        or any(token in evidence.excerpt for token in CONSISTENCY_KEYWORDS.placeholder_evidence_tokens)
        for evidence in item.evidenceRefs
    )


def _infer_genre(text: str) -> str | None:
    normalized = text.strip()
    if not normalized:
        return None
    for genre, keywords in CONSISTENCY_KEYWORDS.genre_keywords.items():
        if any(keyword in normalized for keyword in keywords):
            return genre
    return None
