# HarnessLab Demo

Example output from a local smoke run.

## Command

```bash
harnesslab compare examples/ticket_triage \
  --harness minimal,with_retry \
  --tasks 2 \
  --local \
  --output report.html
```

## Terminal output

```
Evaluating harness: minimal
View the evaluation results for experiment: 'harnesslab-minimal-...' at:
https://smith.langchain.com/...

Evaluating harness: with_retry
View the evaluation results for experiment: 'harnesslab-with_retry-...' at:
https://smith.langchain.com/...

Report written to /path/to/report.html
```

## Report preview

| Harness | task_pass | graph_trajectory | efficiency | failure_fingerprint |
|---|---|---|---|---|
| minimal | 0.50 | 1.00 | 0.85 | 0.50 |
| with_retry | 0.50 | 1.00 | 0.80 | 0.50 |

Scores vary by model and API latency. The comparison table is the primary artifact.

## CI smoke

GitHub Actions runs the same smoke command on `main` pushes:

```bash
harnesslab compare examples/ticket_triage --harness minimal --tasks 2 --local
```

Required repository secret: `OPENAI_API_KEY`
