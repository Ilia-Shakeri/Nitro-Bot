# Release and Version Policy

Nitro Bot uses Semantic Versioning: `MAJOR.MINOR.PATCH`.

Current version: `0.8.0-alpha.1`

## Meaning

- `0.x`: pre-release product. Contracts may still change.
- `alpha`: core flow is incomplete or not proven end to end.
- `beta`: core flow works, but operational or product gates remain.
- `rc`: production candidate. Only release-blocking fixes may enter.
- `1.0.0`: production contract and all roadmap gates are proven.
- Patch: backward-compatible fix.
- Minor: backward-compatible feature or material workflow improvement.
- Major: incompatible public API, data, or operator contract change.

## Source of truth

- `VERSION` is the canonical repository version.
- `frontend/package.json`, `frontend/package-lock.json`,
  `frontend/public/build-info.json`, `.env.example`, `docker-compose.yml`, and
  backend runtime defaults must match `VERSION` before a tag.
- Production should set `APP_VERSION` to the immutable release tag or image
  revision. A restart alone does not reload changed Compose environment values.

## Branch and tag rules

- Work merges into `main` only after required checks pass.
- Release tags use `vMAJOR.MINOR.PATCH` plus an optional pre-release suffix.
- A tag is immutable. A bad tag gets a new patch or pre-release number.
- Do not tag roadmap intent. Tag only a build whose gate has evidence.

Examples:

- `v0.8.0-alpha.1`
- `v0.8.0`
- `v1.0.0-rc.1`
- `v1.0.0`

## Required checks

Every change:

- Backend tests.
- Frontend build, lint, and form checks.
- Migration review when models change.
- No tracked secret or generated private artifact.

Release candidate and stable release:

- PostgreSQL integration tests.
- Compose configuration validation.
- Isolated staging deploy.
- Remote liveness and readiness.
- Telegram bot smoke.
- DMB canary for new release and edit.
- Backup and restore drill.
- Rollback drill.
- Dependency, image, and secret scans.

## Commit style

Use Conventional Commits:

- `feat:` user or operator feature
- `fix:` defect fix
- `refactor:` behavior-preserving code change
- `test:` test-only change
- `docs:` documentation-only change
- `build:` dependency or build change
- `ci:` pipeline change
- `chore:` repository maintenance

Breaking change uses `!`, such as `feat(api)!: replace release payload`.

## Migration order

1. Back up and verify restore evidence.
2. Apply additive schema.
3. Deploy readers that understand old and new data.
4. Deploy writers for new data.
5. Backfill with an idempotent job.
6. Verify counts and invariants.
7. Remove old schema only in a later release.

## Release evidence

Each tagged release needs a short record containing:

- Commit and image digests.
- Migration head.
- Exact test commands and results.
- Staging URL and smoke result.
- DMB test release IDs with private fields redacted.
- Backup timestamp and restore result.
- Known issues.
- Rollback command and owner.

Never put tokens, passwords, payment destinations, receipts, signed URLs, or
customer media in release notes or test evidence.
