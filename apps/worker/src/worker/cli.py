from __future__ import annotations

import argparse
from collections.abc import Sequence

from worker.bootstrap import bootstrap_worker_runtime
from worker.commands import run_batch_command, run_eval_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="worker",
        description="Run regression suites and local batch jobs on the shared evaluation pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    batch_parser = subparsers.add_parser(
        "batch",
        help="Run a local batch source",
        description="Execute a local batch JSON source with the shared scoring pipeline and write a summary report.",
    )
    batch_parser.add_argument(
        "--source",
        default="evals/",
        help="Path to a local batch JSON source.",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the resolved source and runtime without executing.",
    )
    batch_parser.set_defaults(handler=run_batch_command)

    eval_parser = subparsers.add_parser(
        "eval",
        help="Run an eval suite",
        description="Execute an eval suite against the shared scoring pipeline and write report/baseline artifacts.",
    )
    eval_parser.add_argument(
        "--suite",
        default="smoke",
        help="Eval suite name or explicit JSON path.",
    )
    eval_parser.add_argument(
        "--baseline-id",
        default=None,
        help="Optional baseline id for baseline creation or comparison.",
    )
    eval_parser.add_argument(
        "--report-id",
        default=None,
        help="Optional report id override.",
    )
    eval_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the resolved suite and runtime without executing.",
    )
    eval_parser.set_defaults(handler=run_eval_command)

    batch_parser.add_argument(
        "--report-id",
        default=None,
        help="Optional batch summary report id.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    context = bootstrap_worker_runtime(command_name=args.command)
    handler = args.handler
    return handler(args, context)


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
