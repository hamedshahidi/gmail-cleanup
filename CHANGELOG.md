# Changelog

## v0.1.0

Initial public release.

### Features
- Safe Gmail cleanup CLI
- Dry-run query with counts and samples
- Staging mode using Gmail labels
- CSV / JSON export for audit
- Guarded trash command (recoverable)
- Doctor command to diagnose OAuth and local setup

### Safety guarantees
- No deletion without a label
- No deletion without `--execute`
- Typed confirmation required
- Trash only (no permanent delete)

Designed to prevent accidental data loss.
