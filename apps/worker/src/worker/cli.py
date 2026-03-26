from __future__ import annotations

import argparse
from collections.abc import Sequence

from worker.bootstrap import bootstrap_worker_runtime
from worker.commands import run_batch_command, run_eval_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="worker",
        description="Standalone worker CLI skeleton with terminal-only batch and eval placeholders.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    batch_parser = subparsers.add_parser(
        "batch",
        help="Batch placeholder entry",
        description="Run the minimal batch placeholder path. No real batch work or formal eval artifacts are produced.",
    )
    batch_parser.add_argument(
        "--source",
        default="evals/",
        help="Placeholder path for a future batch input source.",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Acknowledge placeholder-only execution. Required in the current skeleton.",
    )
    batch_parser.set_defaults(handler=run_batch_command)

    eval_parser = subparsers.add_parser(
        "eval",
        help="Eval placeholder entry",
        description="Run the minimal eval placeholder path. No real regression, report, or baseline output is produced.",
    )
    eval_parser.add_argument(
        "--suite",
        default="smoke",
        help="Placeholder name for a future eval suite.",
    )
    eval_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Acknowledge placeholder-only execution. Required in the current skeleton.",
    )
    eval_parser.set_defaults(handler=run_eval_command)
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
