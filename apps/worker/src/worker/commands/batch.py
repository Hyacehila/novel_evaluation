from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from worker.bootstrap import WorkerRuntimeContext
from worker.runtime_execution import build_default_report_id, run_batch_source


def run_batch_command(args: Namespace, context: WorkerRuntimeContext) -> int:
    source_path = Path(args.source).resolve()

    print("mode=batch")
    print(f"source={args.source!r}")
    print(f"source_path={str(source_path)!r}")
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
        print("boundary=batch CLI will reuse the shared application scoring pipeline")
        return 0

    if not source_path.exists():
        print(f"error=source_not_found path={str(source_path)!r}")
        return 2

    summary = run_batch_source(
        context=context,
        source_path=source_path,
        report_id=args.report_id or build_default_report_id("batch"),
    )
    print("status=completed")
    print(f"total_count={summary.total_count}")
    print(f"available_count={summary.available_count}")
    print(f"blocked_count={summary.blocked_count}")
    print(f"failed_count={summary.failed_count}")
    print(f"report_path={str(summary.report_path) if summary.report_path is not None else 'null'}")
    return 0
