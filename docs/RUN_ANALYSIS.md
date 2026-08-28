# HarnessLab Run Analysis

Full task-ablation analysis lives in:

**[`analysis/task_ablation_nano_minimal/`](task_ablation_nano_minimal/README.md)**

| File | Contents |
|---|---|
| `README.md` | Full write-up with per-task scores and findings |
| `summary.json` | Aggregated evaluator averages |
| `results.json` | All 9 task rows with outputs and evaluations |
| `manifest.json` | Run metadata |
| `per_task/T-*.json` | One JSON file per ticket |

**Latest run:** `gpt-4.1-nano` + `minimal` harness, dataset `task_ablation`, 9 tasks (T-011–T-019).

To regenerate after a new run:

```bash
python scripts/generate_ablation_analysis.py .harnesslab/runs/<timestamp>_gpt-4-1-nano
```
