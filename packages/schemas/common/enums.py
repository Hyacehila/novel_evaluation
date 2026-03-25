from __future__ import annotations

from enum import StrEnum


class StageName(StrEnum):
    INPUT_SCREENING = "input_screening"
    RUBRIC_EVALUATION = "rubric_evaluation"
    CONSISTENCY_CHECK = "consistency_check"
    AGGREGATION = "aggregation"
    FINAL_PROJECTION = "final_projection"


class InputComposition(StrEnum):
    CHAPTERS_OUTLINE = "chapters_outline"
    CHAPTERS_ONLY = "chapters_only"
    OUTLINE_ONLY = "outline_only"


class EvaluationMode(StrEnum):
    FULL = "full"
    DEGRADED = "degraded"


class Sufficiency(StrEnum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    MISSING = "missing"


class StageStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"
    UNRATEABLE = "unrateable"


class EvidenceSourceType(StrEnum):
    CHAPTERS = "chapters"
    OUTLINE = "outline"
    CROSS_INPUT = "cross_input"


class ScoreBand(StrEnum):
    ZERO = "0"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"


class AxisId(StrEnum):
    HOOK_RETENTION = "hookRetention"
    SERIAL_MOMENTUM = "serialMomentum"
    CHARACTER_DRIVE = "characterDrive"
    NARRATIVE_CONTROL = "narrativeControl"
    PACING_PAYOFF = "pacingPayoff"
    SETTING_DIFFERENTIATION = "settingDifferentiation"
    PLATFORM_FIT = "platformFit"
    COMMERCIAL_POTENTIAL = "commercialPotential"


class SkeletonDimensionId(StrEnum):
    MARKET_ATTRACTION = "marketAttraction"
    NARRATIVE_EXECUTION = "narrativeExecution"
    CHARACTER_MOMENTUM = "characterMomentum"
    NOVELTY_UTILITY = "noveltyUtility"


class FatalRisk(StrEnum):
    AI_MANUAL_TONE = "aiManualTone"
    STALE_FORMULA = "staleFormula"
    CONCEPT_SPAM = "conceptSpam"
    FAKE_PAYOFF = "fakePayoff"
    NON_NARRATIVE_SUBMISSION = "nonNarrativeSubmission"
    INSUFFICIENT_MATERIAL = "insufficientMaterial"


class SubmissionSourceType(StrEnum):
    DIRECT_INPUT = "direct_input"
    FILE_UPLOAD = "file_upload"
    HISTORY_DERIVED = "history_derived"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultStatus(StrEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    BLOCKED = "blocked"


class TopLevelScoreField(StrEnum):
    SIGNING_PROBABILITY = "signingProbability"
    COMMERCIAL_VALUE = "commercialValue"
    WRITING_QUALITY = "writingQuality"
    INNOVATION_SCORE = "innovationScore"
