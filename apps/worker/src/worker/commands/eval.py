from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from worker.bootstrap import WorkerRuntimeContext
from worker.runtime_execution import build_default_report_id, resolve_suite_path, run_eval_suite


def run_eval_command(args: Namespace, context: WorkerRuntimeContext) -> int:
    suite_path = resolve_suite_path(evals_root=context.evals_root, suite_name=args.suite)
    report_id = args.report_id or build_default_report_id("eval")

    print("mode=eval")
    print(f"suite={args.suite!r}")
    print(f"suite_path={str(suite_path)!r}")
    print(f"dry_run={args.dry_run}")
    print(
        "runtime="
        f"provider:{context.runtime_metadata.provider_id},"
        f"model:{context.runtime_metadata.model_id},"
        f"prompt:{context.runtime_metadata.prompt_version},"
        f"schema:{context.runtime_metadata.schema_version},"
        f"rubric:{context.runtime_metadata.rubric_version}"
    )
    print(f"api_handoff_enabled={context.api_handoff_enabled}")
    print(f"real_execution_enabled={context.real_execution_enabled}")
    if args.dry_run:
        print("status=dry_run")
        print("boundary=eval CLI will reuse the shared application scoring pipeline")
        return 0

    if not suite_path.exists():
        print(f"error=suite_not_found path={str(suite_path)!r}")
        return 2

    baseline_path, report_path, records_path = run_eval_suite(
        context=context,
        suite_path=suite_path,
        report_id=report_id,
        baseline_id=args.baseline_id,
    )
    print("status=completed")
    print(f"report_id={report_id!r}")
    print(f"baseline_id={args.baseline_id!r}")
    print(f"baseline_path={str(baseline_path) if baseline_path is not None else 'null'}")
    print(f"report_path={str(report_path)!r}")
    print(f"records_path={str(records_path)!r}")
    return 0
