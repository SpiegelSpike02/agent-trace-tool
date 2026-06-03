"""Command-line interface for the Agent trajectory analyzer."""

from __future__ import annotations

import argparse
import json
import sys

from .evaluator import evaluate_file
from .parser import LogParseError, parse_jsonl
from .render import render_text_tree, traces_to_payload, write_payload


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    commands = {"parse", "evaluate"}
    if raw_argv and raw_argv[0] not in commands and not raw_argv[0].startswith("-"):
        raw_argv.insert(0, "parse")

    parser = argparse.ArgumentParser(description="Agent trace parser, analyzer and evaluation harness.")
    subparsers = parser.add_subparsers(dest="command")

    parse_parser = subparsers.add_parser("parse", help="Parse Agent JSONL logs into a trace tree payload.")
    parse_parser.add_argument("input", help="Path to a JSONL trace log.")
    parse_parser.add_argument("--out", help="Write JSON payload to this file.")
    parse_parser.add_argument("--js-var", help="Wrap output as window.<name> = payload for static demos.")
    parse_parser.add_argument("--tree", action="store_true", help="Print a compact text tree instead of JSON.")

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate traces against a case spec.")
    eval_parser.add_argument("input", help="Path to a JSONL trace log.")
    eval_parser.add_argument("--cases", required=True, help="Path to an evaluation cases JSON file.")
    eval_parser.add_argument("--out", help="Write evaluation report JSON to this file.")

    args = parser.parse_args(raw_argv)
    if args.command == "evaluate":
        return _evaluate(args)

    if args.command is None and not getattr(args, "input", None):
        parser.print_help()
        return 0

    return _parse(args)


def _parse(args: argparse.Namespace) -> int:
    try:
        traces = parse_jsonl(args.input)
    except LogParseError as exc:
        print(f"parse error: {exc}", file=sys.stderr)
        return 2

    if args.tree:
        print("\n\n".join(render_text_tree(trace) for trace in traces))
        return 0

    payload = traces_to_payload(traces)
    if args.out:
        write_payload(args.out, payload, js_var=args.js_var)
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.js_var:
            text = f"window.{args.js_var} = {text};"
        print(text)
    return 0


def _evaluate(args: argparse.Namespace) -> int:
    try:
        report = evaluate_file(args.input, args.cases)
    except (LogParseError, ValueError, OSError) as exc:
        print(f"evaluation error: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        write_payload(args.out, report)
    else:
        print(text)
    return 0 if report["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
