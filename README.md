# Mad Mallard Backup Proof

[![License](https://img.shields.io/github/license/drakeg/madmallard-backup-proof)](https://github.com/drakeg/madmallard-backup-proof/blob/main/LICENSE)


A fixed-scope **Prove Your Backup Works** recovery drill for small agencies.

**Pilot hypothesis:** $349 for one app, one database, one approved snapshot (up to 10 GiB). No production failover, recovery-time guarantee, ongoing monitoring, or out-of-scope repairs.

## Synthetic demonstration

Requires Python 3.10+ (stdlib only). Run:

```bash
python3 scripts/drill.py
```

Evidence is written to `reports/latest.json` and `reports/latest.md` (ignored by git). The demo creates a consistent SQLite backup using SQLite's online backup API, restores it into a temporary directory, launches an application against the restored DB, and checks database integrity, record retrieval, count, and application health. It does **not** use customer data.

## Production safety model

Never mount a production database or Docker socket into the drill. Require written authorization, approved backup export, scope, retention period and three acceptance checks. For PostgreSQL use pg_dump/pg_restore; for MySQL use a supported consistent logical dump. Never copy live database files casually. Run customer restores in a dedicated isolated environment with no production credentials, isolated networking, encrypted storage and secure cleanup.

Restic support is planned as a separate adapter: `restic check` alone is not recovery proof; a real restore and functional validation are mandatory. No claim is made that this initial synthetic demo uses Restic.

## Commercial validation

First 24h: synthetic demo, one-page evidence sample, $349 fixed-scope offer, five qualified prospect names (no outreach). Next 24h: outreach only after approval. Go after two substantive conversations and one written paid pilot acceptance. Stop/revise after five qualified conversations without commitment or recurring requests for production guarantees.

## Roadmap

1. Restic repository restore adapter with safe path allowlisting and size checks
2. Configurable HTTP and database acceptance checklist
3. Markdown/PDF report, dependency inventory, sanitized runbook
4. Ephemeral Docker Compose runner, cleanup and CI
5. Prospect research (list only), pilot onboarding checklist

No secrets or customer backups should be committed.
