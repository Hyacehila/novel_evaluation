from __future__ import annotations

from argparse import Namespace

from worker.bootstrap import WorkerRuntimeContext


def run_batch_command(args: Namespace, context: WorkerRuntimeContext) -> int:
    if not args.dry_run:
        print("error=batch skeleton requires explicit --dry-run")
        return 2

    print("mode=batch")
    print("status=placeholder")
    print(f"dry_run={args.dry_run}")
    print(f"source={args.source!r}")
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
    print("boundary=placeholder-only batch CLI; no apps/api in-process task handoff")
    print("next_step=real batch execution, EvalRecord writes, and report artifacts arrive in a later wave")
    return 0
