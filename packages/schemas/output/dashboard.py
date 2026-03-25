from __future__ import annotations

from packages.schemas.common.base import MetaData, SchemaModel
from packages.schemas.output.task import EvaluationTaskSummary, RecentResultSummary


class DashboardSummary(SchemaModel):
    recentTasks: list[EvaluationTaskSummary]
    activeTasks: list[EvaluationTaskSummary]
    recentResults: list[RecentResultSummary]


class HistoryList(SchemaModel):
    items: list[EvaluationTaskSummary]
    meta: MetaData
