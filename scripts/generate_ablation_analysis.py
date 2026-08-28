#!/usr/bin/env python3
"""Generate task ablation analysis folder from a local HarnessLab run."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

METRICS = [
    "task_pass",
    "tool_sequence",
    "graph_trajectory",
    "failure_fingerprint",
    "efficiency",
    "error_recovery",
    "step_count",
    "reply_text",
]

STRESS = {
    "T-011": "Flaky read_ticket (2 failures)",
    "T-012": "14-turn conversation context recall",
    "T-013": "Merged-account billing dispute",
    "T-014": "Dual KB search required",
    "T-015": "Flaky search_kb (2 failures)",
    "T-016": "Priority SLA + escalate",
    "T-017": "Category trap (billing → account)",
    "T-018": "Tool budget + flaky search_kb/escalate",
    "T-019": "Adversarial prompt (sync vs billing)",
}


def _load_run(run_dir: Path) -> tuple[dict, dict, list]:
    rows = json.loads((run_dir / "gpt-4-1-nano.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    manifest = json.loads((run_dir / "manifest.json").read_text())
    return manifest, summary, rows


def _task_row(record: dict) -> dict:
    tid = record["inputs"]["ticket_id"]
    ev = record["evaluation_results"]
    out = record["outputs"]
    details = out.get("details") or {}
    reply_ev = ev.get("reply_text") or ev.get("final_reply") or {}
    reply = (
        reply_ev.get("comment")
        or reply_ev.get("value")
        or details.get("final_reply")
        or out.get("final_reply")
        or ""
    )
    return {
        "tid": tid,
        "task_pass": ev["task_pass"]["score"],
        "tool_seq": ev["tool_sequence"]["score"],
        "graph": ev["graph_trajectory"]["score"],
        "fp": ev["failure_fingerprint"]["comment"],
        "output": out.get("classification") or out.get("output", ""),
        "reply": reply,
        "task_comment": ev["task_pass"]["comment"],
        "tool_comment": ev["tool_sequence"]["comment"],
        "graph_comment": ev["graph_trajectory"]["comment"],
        "eff_comment": ev["efficiency"]["comment"],
    }


def build_markdown(manifest: dict, summary: dict, rows: list[dict], run_dir: Path) -> str:
    arm = next(iter(summary))
    avg = summary[arm]
    task_rows = [_task_row(r) for r in sorted(rows, key=lambda r: r["inputs"]["ticket_id"])]

    passed = [t for t in task_rows if t["task_pass"] == 1.0]
    failed = [t for t in task_rows if t["task_pass"] == 0.0]
    partial = [t for t in task_rows if 0 < t["task_pass"] < 1.0]

    lines: list[str] = [
        "# Task Ablation Analysis — gpt-4.1-nano + minimal",
        "",
        "**Generated:** 2026-08-28",
        f"**Run:** `{run_dir.name}`",
        f"**Dataset:** `{manifest.get('dataset', 'task_ablation')}`",
        f"**Model:** `{manifest.get('model')}` | **Harness:** `{manifest.get('harness')}`",
        "**Tasks:** T-011 through T-019 (9 stress tasks)",
        "",
        "---",
        "",
        "## Executive summary",
        "",
        "| Metric | Average |",
        "|---|---:|",
    ]
    for key in METRICS:
        if key in avg:
            lines.append(f"| **{key}** | **{avg[key]:.2f}** |")

    partial_str = ", ".join(f"{t['tid']} ({t['task_pass']:.2f})" for t in partial) or "none"
    lines.extend(
        [
            "",
            f"- **Full passes (task_pass=1.0):** {len(passed)} — {', '.join(t['tid'] for t in passed) or 'none'}",
            f"- **Partial credit:** {len(partial)} — {partial_str}",
            f"- **Hard failures (task_pass=0.0):** {len(failed)} — {', '.join(t['tid'] for t in failed) or 'none'}",
            "",
            "---",
            "",
            "## Per-task results",
            "",
            "| Ticket | output | task_pass | tool_sequence | graph_trajectory | failure |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for t in task_rows:
        lines.append(
            f"| **{t['tid']}** | `{t['output'] or '(empty)'}` | {t['task_pass']:.2f} | "
            f"{t['tool_seq']:.2f} | {t['graph']:.2f} | {t['fp']} |"
        )

    lines.extend(["", "---", "", "## Per-task detail", ""])
    for t in task_rows:
        reply_display = t["reply"].replace("\n", " ")[:200] if t["reply"] else "*(empty — no draft_reply)*"
        lines.extend(
            [
                f"### {t['tid']} — {STRESS.get(t['tid'], '')}",
                "",
                "| Field | Value |",
                "|---|---|",
                f"| Classification (output) | `{t['output'] or '(empty)'}` |",
                f"| final_reply | {reply_display} |",
                f"| task_pass | {t['task_pass']:.2f} — `{t['task_comment']}` |",
                f"| tool_sequence | {t['tool_seq']:.2f} — `{t['tool_comment']}` |",
                f"| graph_trajectory | {t['graph']:.2f} — `{t['graph_comment']}` |",
                f"| failure_fingerprint | {t['fp']} |",
                f"| efficiency | `{t['eff_comment']}` |",
                "",
            ]
        )

    lines.extend(["---", "", "## Task difficulty ranking (by task_pass)", ""])
    for index, t in enumerate(sorted(task_rows, key=lambda x: -x["task_pass"]), 1):
        lines.append(f"{index}. **{t['tid']}** — {t['task_pass']:.2f} ({STRESS.get(t['tid'], '')})")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Manifest",
            "",
            "```json",
            json.dumps(manifest, indent=2),
            "```",
            "",
            "## Summary scores",
            "",
            "```json",
            json.dumps(summary, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_analysis(run_dir: Path, out_dir: Path) -> Path:
    manifest, summary, rows = _load_run(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(build_markdown(manifest, summary, rows, run_dir) + "\n")
    shutil.copy2(run_dir / "manifest.json", out_dir / "manifest.json")
    shutil.copy2(run_dir / "summary.json", out_dir / "summary.json")
    shutil.copy2(run_dir / "gpt-4-1-nano.json", out_dir / "results.json")
    per_task = out_dir / "per_task"
    per_task.mkdir(exist_ok=True)
    for record in sorted(rows, key=lambda r: r["inputs"]["ticket_id"]):
        tid = record["inputs"]["ticket_id"]
        (per_task / f"{tid}.json").write_text(json.dumps(record, indent=2) + "\n")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task ablation analysis from a local run.")
    parser.add_argument("run_dir", type=Path, help="Path to .harnesslab/runs/<timestamp>_gpt-4-1-nano")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("analysis/task_ablation_nano_minimal"),
        help="Output analysis directory",
    )
    args = parser.parse_args()
    path = write_analysis(args.run_dir.resolve(), args.out.resolve())
    print(path)


if __name__ == "__main__":
    main()
