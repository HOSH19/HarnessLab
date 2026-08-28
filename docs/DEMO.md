# HarnessLab Demo

Example output from a local compare run (default: 2 harnesses × 2 tasks).

## Command

```bash
harnesslab compare examples/ticket_triage \
  --harness minimal,retry \
  --tasks 2 \
  --local \
  --output report.html
```

## Terminal output

```
Evaluating harness: minimal
View the evaluation results for experiment: 'minimal-...' at:
https://smith.langchain.com/...

Evaluating harness: retry
View the evaluation results for experiment: 'retry-...' at:
https://smith.langchain.com/...

Report written to /path/to/report.html
```

## Report preview

| Harness | task_pass | graph_trajectory | efficiency | failure_fingerprint |
|---|---|---|---|---|
| minimal | 0.50 | 1.00 | 0.85 | 0.50 |
| retry | 0.50 | 1.00 | 0.80 | 0.50 |

Scores vary by model and API latency. The comparison table is the primary artifact.

## CI compare

GitHub Actions runs a single-task local compare on `main` pushes:

```bash
harnesslab compare examples/ticket_triage --harness minimal --tasks 2 --local
```

Required repository secret: `OPENAI_API_KEY`
