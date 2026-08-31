# Regression gate

`benchmark` and `gate` compare harness arms locally by default. They do not require LangSmith credentials unless you pass `--no-local`.

Use them to catch score regressions in CI without paying for experiment uploads on every PR check.

---

## How it works

1. **`benchmark`** runs a harness compare and writes per-arm evaluator averages to a JSON file.
2. **`gate`** runs the same compare, bootstraps per-task score deltas, and exits non-zero when `task_pass` or `error_recovery` regresses beyond a threshold.

Both commands use the same in-memory evaluation path as `compare --local`. LangSmith is optional (`--no-local`).

---

## Export a baseline

```bash
python -m harnesslab benchmark examples/incident_manager \
  --harness minimal,retry \
  --tasks 6 \
  --local \
  -o benchmarks/incident-manager.json
```

Commit `benchmarks/incident-manager.json` to the repo as your golden reference.

---

## Run the gate

```bash
python -m harnesslab gate examples/incident_manager \
  --baseline benchmarks/incident-manager.json \
  --harness minimal,retry \
  --tasks 6 \
  --local
```

Exit code `0` means pass. Exit code `1` means a blocking evaluator regressed.

---

## Verify it works (smoke test)

**Pass case** (baseline matches current run):

```bash
# 1. Export baseline from one task (fast)
python -m harnesslab benchmark examples/incident_manager \
  --harness minimal,retry --task I-101 --local -o /tmp/baseline.json

# 2. Gate should pass immediately
python -m harnesslab gate examples/incident_manager \
  --baseline /tmp/baseline.json --harness minimal,retry --task I-101 --local
```

**Fail case** (edit baseline to force regression):

```bash
# Lower task_pass in the baseline file, then re-run gate
python -m harnesslab gate examples/incident_manager \
  --baseline /tmp/baseline.json --harness minimal,retry --task I-101 --local
# Expect: REGRESSION: ... and exit code 1
```

---

## LangSmith mode (optional)

`gate` and `benchmark` can upload experiments when you omit `--local`:

```bash
python -m harnesslab benchmark examples/incident_manager \
  --harness cache,circuit_breaker --tasks 6 --no-local \
  -o benchmarks/incident-manager.json
```

You still need `OPENAI_API_KEY` and `LANGSMITH_API_KEY` in `.env`. The gate decision itself always reads the in-memory compare results, not the LangSmith API.

---

## Options

| Flag | Default | Purpose |
|---|---|---|
| `--baseline` | required for `gate` | Path to baseline JSON |
| `-o` / `--output` | required for `benchmark` | Where to write baseline JSON |
| `--harness` | `minimal,retry` | Comma-separated harness names |
| `--tasks` | `1` | Number of stress tasks |
| `--task` | none | Single task id (e.g. `I-101`) |
| `--max-regression` | `0.05` | Max allowed score drop for blocking evaluators |
| `--local` / `--no-local` | `--local` | Skip or enable LangSmith upload |

Blocking evaluators: `task_pass`, `error_recovery`. See [EVALUATORS.md](EVALUATORS.md).
