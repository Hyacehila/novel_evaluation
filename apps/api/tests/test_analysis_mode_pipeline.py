from __future__ import annotations

import json

from packages.application.scoring_pipeline.orchestration import ScoringPipeline
from packages.schemas.common.enums import AxisId, EvaluationMode, InputComposition, StageName
from packages.schemas.input.joint_submission import JointSubmissionRequest

from tests.test_scoring_pipeline import (
    RecordingPromptRuntime,
    RecordingProviderAdapter,
    build_aggregation_result,
    build_pipeline_provider_payloads,
    build_rubric_slice_payload,
    build_screening_result,
    build_task,
    build_type_classification_result,
    build_type_lens_result,
)


def build_long_opening_outline_submission() -> JointSubmissionRequest:
    return JointSubmissionRequest.model_validate(
        {
            "title": "长篇开篇测试",
            "analysisMode": "long_opening_outline",
            "chapters": [
                {
                    "title": "第一章",
                    "content": "宗门大阵熄灭后，主角被迫在七天内查明叛徒并赢下大比。",
                }
            ],
            "outline": {"content": "后续围绕宗门大比、秘境夺宝和修复护山大阵推进。"},
            "sourceType": "direct_input",
        }
    )


def build_completed_fulltext_submission() -> JointSubmissionRequest:
    return JointSubmissionRequest.model_validate(
        {
            "title": "已完成全文测试",
            "analysisMode": "completed_fulltext",
            "chapters": [
                {
                    "title": "全文",
                    "content": "主角从港城审判开局，历经听证、封港、董事会改组，最终揭开走私案并完成结局。",
                }
            ],
            "sourceType": "direct_input",
        }
    )


def test_scoring_pipeline_long_opening_outline_uses_formal_prompts_only() -> None:
    submission = build_long_opening_outline_submission()
    screening = build_screening_result()
    type_classification = build_type_classification_result(
        input_composition=screening.inputComposition,
        evaluation_mode=screening.evaluationMode,
    )
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=screening,
            type_classification=type_classification,
            type_lens=build_type_lens_result(
                novel_type=type_classification.novelType,
                input_composition=screening.inputComposition,
                evaluation_mode=screening.evaluationMode,
            ),
            rubric_payload=lambda request: build_rubric_slice_payload(
                requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]
            ),
            aggregation_payload=build_aggregation_result().model_dump(mode="json"),
        )
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    result = pipeline.run(task=build_task(), submission=submission)

    assert result.projection.overall.score == 75
    assert {call["analysis_mode"] for call in prompt_runtime.calls} == {"long_opening_outline"}
    assert {request.promptId for request in provider.requests} == {"prompt-test"}
    assert [request.stage for request in provider.requests].count(StageName.RUBRIC_EVALUATION) == 3


def test_scoring_pipeline_completed_fulltext_uses_formal_prompts_only() -> None:
    submission = build_completed_fulltext_submission()
    screening_payload = {
        "taskId": "task_pipeline_001",
        "stage": "input_screening",
        "schemaVersion": "schema-test-v1",
        "promptVersion": "prompt-test-v1",
        "rubricVersion": "rubric-test-v1",
        "providerId": "provider-test",
        "modelId": "model-test",
        "analysisMode": "completed_fulltext",
        "inputComposition": "chapters_only",
        "hasChapters": True,
        "hasOutline": False,
        "chaptersSufficiency": "sufficient",
        "outlineSufficiency": "missing",
        "evaluationMode": "full",
        "rateable": True,
        "status": "ok",
        "rejectionReasons": [],
        "riskTags": [],
        "segmentationPlan": None,
        "confidence": 0.9,
        "continueAllowed": True,
    }
    type_classification = build_type_classification_result(
        input_composition=InputComposition.CHAPTERS_ONLY,
        evaluation_mode=EvaluationMode.FULL,
    )
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening_payload,
            StageName.TYPE_CLASSIFICATION: type_classification.model_dump(mode="json"),
            StageName.TYPE_LENS_EVALUATION: build_type_lens_result(
                novel_type=type_classification.novelType,
                input_composition=InputComposition.CHAPTERS_ONLY,
                evaluation_mode=EvaluationMode.FULL,
            ).model_dump(mode="json"),
            StageName.RUBRIC_EVALUATION: lambda request: build_rubric_slice_payload(
                requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]
            ),
            StageName.AGGREGATION: build_aggregation_result().model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    result = pipeline.run(
        task=build_task(
            evaluation_mode=EvaluationMode.FULL,
            input_composition=InputComposition.CHAPTERS_ONLY,
        ),
        submission=submission,
    )

    assert result.projection.overall.score == 75
    assert {call["analysis_mode"] for call in prompt_runtime.calls} == {"completed_fulltext"}
    assert {request.promptId for request in provider.requests} == {"prompt-test"}
