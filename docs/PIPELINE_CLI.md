# Profile Pipeline CLI

This project uses one CLI entry point for pipeline tasks:

```bash
python scripts/profile_cli.py <command> [flags]
```

## Main Commands

- `generate-profile --validate`
  - Builds SVG assets, dashboard JSON, and README.
  - Runs contract validation when `--validate` is set.
  - Optional fixture mode: `--fixture tests/fixtures/sample_collected_data.json` (no live API calls).

- `check-metrics --path metrics.general.svg`
  - Checks key values in the metrics SVG card.
  - Treats repository count as required.
  - Treats stargazer and release drift as warnings by default.

- `validate`
  - Validates generated outputs and snapshot contract.

- `doctor`
  - Runs local environment checks.
  - Writes `site/data/doctor_report.json`.

- `triage --workflow "Generate Metrics" --limit 20`
  - Builds machine-friendly triage report with findings.
  - Writes `site/data/triage_report.json`.
  - Supports `--fail-on <severity>`.

- `triage-summary --input site/data/triage_report.json`
  - Prints a deterministic, severity-ranked fix order.
  - Supports `--min-severity` and `--limit`.

- `audit-runs --workflow "Generate Metrics"`
  - Prints workflow run summary from GitHub Actions.

- `branch-protection --repo owner/repo --apply --fail-on-missing`
  - Audits required checks on a branch.
  - Can apply missing required checks with `gh api`.

## AI Ingestion Contract

`site/data/triage_report.json` is the stable handoff for AI tools.

- `schema.name`: `profile_triage_report`
- `schema.version`: `1.0.0`
- `findings[]` fields:
  - `finding_id`
  - `severity`
  - `status`
  - `evidence`
  - `likely_cause`
  - `fix_hint`
  - `confidence`

Use this report as input for AI summaries and fix-priority recommendations instead of parsing raw workflow logs.

## Diagnostics Files

Every CLI command writes diagnostics:

- latest: `site/data/run_diagnostics.json`
- history: `site/data/run_diagnostics_history.jsonl`

Each entry includes:

- command
- exit code
- token mode
- cache mode
- warnings and errors

## Source of Truth

- Canonical data: `site/data/profile_snapshot.json`
- Visual card only: `metrics.general.svg`

CI should fail on snapshot contract errors, not third-party card drift.
