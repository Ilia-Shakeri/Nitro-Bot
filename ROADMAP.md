# Nitro Bot Roadmap

Current release: `0.9.0-alpha.7`

Target release: `1.0.0`

This roadmap is ordered by user money, release correctness, and data safety. A
version is complete only when every exit gate for that version has evidence.
Passing unit tests alone does not complete a version.

## Release train

| Version | Goal | Exit result |
| --- | --- | --- |
| `0.8.0-alpha.1` | Audited baseline | Version contract and delivery plan exist |
| `0.8.0-alpha.2` | Durable release work | Restart-safe media jobs and exact-once failure refund exist |
| `0.8.0-alpha.3` | Safe release input | Upload, metadata, genre, URL, and state bounds exist |
| `0.8.0` | Safe state and money flow | No charged release can be lost or falsely reported |
| `0.9.0-alpha.1` | Safe DMB create contract | Isolated jobs, leases, submit proof, and manual review exist |
| `0.9.0-alpha.2` | Complete DMB create wizard | Every specified create step and circuit breaker exist |
| `0.9.0-alpha.3` | Harden DMB input and build | Exact DMB choices, account state, edit gate, and image CI exist |
| `0.9.0-alpha.4` | Match live DMB form | Navigation, dates, labels, roles, and exact suggestions match the live site |
| `0.9.0-alpha.5` | Harden live DMB input | Contributor blur, role select, and direct track upload avoid destructive UI actions |
| `0.9.0-alpha.6` | Protect money and staff actions | Immutable ledger, staff allowlist, audit log, claim idempotency, and durable notices exist |
| `0.9.0-alpha.7` | Bind DMB submission evidence | Pre-submit EAN, ISRC, title, and fingerprint survive crashes and block mismatched completion |
| `0.9.0` | Correct DMB delivery | New and edited releases reach the right DMB state |
| `0.9.1` | Safe payment and support operations | Only allowed staff can mutate money or contact users |
| `0.9.2` | Operable deployment | Health, retry, alert, backup, and recovery work |
| `0.9.3` | Product and legal completion | User flows, policy, retention, and support are complete |
| `1.0.0-rc.1` | Production candidate | Full staging evidence exists |
| `1.0.0` | Production release | Production smoke, rollback, and recovery gates pass |

## `0.8.0-alpha.1` - audited baseline

Scope:

- Adopt Semantic Versioning.
- Mark the product as pre-release, not production-ready.
- Keep one canonical version in `VERSION` and mirror it in runtime build data.
- Publish this roadmap and the release rules in `RELEASE_POLICY.md`.

Exit gates:

- Backend unit suite passes.
- Frontend build, lint, and form checks pass.
- Repository has no unintended changes.

## `0.8.0` - safe state and money flow

Delivered in `0.8.0-alpha.2`:

- Database-backed media and notice jobs with leases, bounded retry, and dead state.
- Restart recovery for legacy staging releases.
- Atomic release charge and job creation.
- Idempotent terminal failure refund with a recorded ledger row.
- Future-dated Telegram login rejection.

Delivered in `0.8.0-alpha.3`:

- Chunked upload reads that stop one byte after the configured hard limit.
- Bounded song, artist, producer, legal-name, mapping, and submission fields.
- Strict Spotify and Apple Music artist host and path validation.
- One shared genre tree enforced by both frontend and backend.
- Database checks for non-negative credits, release cost, job attempts, and allowed states.

Still required before `0.8.0`:

- Immutable idempotency keys and release links on every ledger mutation.
- Notice replay without duplicate remote messages.
- Payment quote validation before receipt upload.
- PostgreSQL concurrency, restart, crash, and notice replay tests.
- Safe orphan-object retention job.

### Durable release jobs

- Replace in-process media tasks with a durable database or Redis-backed job.
- Store job attempts, lease owner, lease expiry, next retry time, and last error.
- Recover expired `staging` and `processing` jobs after restart.
- Add bounded retry and a dead-letter state.
- Make job claim and state transition atomic.
- Add an outbox for Telegram notices. Retry notice delivery without duplicating
  the release or charge.

### Money invariants

- Give every balance mutation an immutable ledger row and idempotency key.
- Link release charge and refund rows to the release ID.
- Refund all terminal processing failures exactly once.
- Never say "refunded" unless the refund ledger row committed.
- Stop a failed notification from hiding a pending payment from staff.
- Add database constraints for allowed states and non-negative values.

### Input and storage safety

- Enforce length limits for song, artist, producer, legal name, email, URL, and
  Telegram caption inputs.
- Validate genre/subgenre pairs on the backend.
- Validate Spotify and Apple Music host and path rules.
- Reject Telegram auth dates too far in the future.
- Stream uploads with a hard byte limit instead of reading unbounded input.
- Validate payment quotes before uploading any receipt.
- Track object ownership and remove orphan uploads with a safe retention job.

Tests:

- Restart during media conversion.
- Duplicate release submission.
- Concurrent charge and refund.
- Worker crash after claim.
- Telegram notice failure and replay.
- Invalid, expired, and reused payment quote.
- PostgreSQL integration tests for row locks and unique constraints.

Exit gates:

- Every accepted release reaches a recoverable durable state.
- Every terminal failed release has one refund or a recorded zero-cost reason.
- Fault-injection tests pass for restart, timeout, and duplicate delivery.

Rollback:

- Keep old read paths during migration.
- Deploy additive schema first, then workers, then API writers.
- Roll back writers before removing any new schema.

## `0.9.0` - correct DMB delivery

Delivered in `0.9.0-alpha.1`:

- Per-release JSON jobs replace the shared SQLite handoff in the live worker.
- Atomic claim, lease, heartbeat, attempt limit, and expired-lease recovery.
- Final Save checkpoint and fail-closed `dmb_verification_required` state.
- Completed state requires DMB release ID, EAN/UPC, ISRC, URL, and screenshot evidence.
- Audited manual resolution can complete, retry, or fail an uncertain delivery.
- Create and edit feature flags default off; edit delivery remains blocked.
- Contract tests and Robot dry-run cover the local handoff and evidence path.

This alpha does not close the `0.9.0` exit gates. Real DMB staging evidence is
still required.

Delivered in `0.9.0-alpha.2`:

- Exact 3000x3000 JPEG cover preparation and WAV input verification.
- Explicit DMB mapping for every mini-app genre and subgenre.
- Label, language, dates, price codes, re-release C year, and current P year.
- Existing-account and new Performer contributor paths.
- Add Tracks, Worldwide, all-platform, review, and exact final Save steps.
- State-based waits replace fixed sleeps in the create page workflow.
- Persistent circuit breaker opens after bounded failures or any uncertain Save.
- PNG screenshot content is validated before completion evidence is accepted.

This alpha still needs an authenticated DMB staging run. Login selectors were
checked against the live public login page; authenticated wizard selectors and
final submission were not exercised.

### New release workflow

- Replace the shared SQLite handoff with a per-job payload or isolated job file.
- Carry every required field: all artists and roles, producers, legal names,
  genre, subgenre, release dates, re-release flag, mappings, profile email,
  explicit flag, and copyright request.
- Submit the final DMB form. Do not treat a filled form as success.
- Verify the DMB success page and capture EAN/UPC, ISRC, DMB release ID, and
  final status.
- Store sanitized execution evidence and screenshot paths.
- Detect partial creation before retry to prevent duplicate albums.

### Edit workflow

- Define which DMB fields can be edited after delivery.
- Use the source DMB release ID.
- Build a distinct edit path. Never create a new album for an edit order.
- Reject impossible edits before charging the user.
- Store an audit diff between source and requested values.

### Automation hardening

- Replace fixed sleeps with state-based waits.
- Centralize selectors and record the DMB page version seen by the worker.
- Detect login, validation, upload, session expiry, and final-submit failures.
- Add a circuit breaker when DMB layout changes.
- Keep failed jobs available for safe staff retry.

Tests:

- Contract tests for the API-to-worker payload.
- Robot dry-run with required environment validation.
- Staging test for one normal release, one re-release, one multi-artist release,
  one new-profile release, one explicit release, and one edit.
- Duplicate-submit recovery test.

Exit gates:

- DMB staging returns and stores real IDs for all test cases.
- A completed state always has DMB evidence.
- An edit changes the intended source release and creates no duplicate.

Rollback:

- Feature-flag new and edit delivery separately.
- Stop new claims before rolling back the worker.
- Keep claimed jobs leased until the old worker is safe to resume.

## `0.9.1` - safe payment and support operations

### Staff authorization

- Require an explicit staff allowlist for payment decisions and ticket replies.
- Validate callback shape, action, transaction state, chat, topic, and actor.
- Bind ticket reply markers to the real ticket owner.
- Store actor ID, action time, old state, and new state in an audit log.
- Remove or disable action buttons after a final decision.

### Payment proof

- Require receipt evidence for card payments.
- Require transaction hash or receipt evidence for manual crypto claims.
- Validate asset, network, quoted amount, destination, quote expiry, and proof
  uniqueness before approval.
- Add idempotency to receipt submission and staff approval.
- Reconcile Stars charges by provider charge ID.
- Define and test refund and dispute handling.
- Add abuse limits for referrals and repeated payment claims.

### Support workflow

- Let a user reply to an existing open ticket.
- Add ticket states: open, waiting_staff, waiting_user, resolved, closed.
- Keep message delivery retry separate from message persistence.

Exit gates:

- Unauthorized group members cannot change money or send staff replies.
- Duplicate callbacks and provider events produce one result.
- Every manual payment has reviewable proof and an audit record.

## `0.9.2` - operable deployment

### Runtime

- Add `/health/live` and `/health/ready` endpoints.
- Readiness must check PostgreSQL, Redis, object storage, and required settings.
- Add health checks for backend, frontend, MinIO, and the worker.
- Decide whether Caddy is part of this Compose project or a documented external
  gateway. Make first deploy work from written commands.
- Pin container images by tested version or digest.
- Lock Python and worker dependencies with hashes.
- Keep the Telegram polling process singleton or split it from the API service.

### Observability

- Emit structured logs with request, release, transaction, job, and attempt IDs.
- Add metrics for queue age, retries, failures, refunds, pending payments,
  notification failures, and DMB duration.
- Add alerts for stuck jobs, failed backups, low storage, and repeated DMB error.
- Redact tokens, credentials, user receipts, and signed object URLs.

### Backup and recovery

- Back up PostgreSQL and MinIO data.
- Encrypt backups and define retention.
- Test restore into an isolated stack.
- Write recovery runbooks for database, object storage, Redis, and DMB jobs.
- Measure recovery point and recovery time.

Exit gates:

- Fresh-host deployment follows the runbook without hidden setup.
- Remote health checks pass.
- Alert drills and isolated restore pass.
- A rollback keeps accepted jobs and user money intact.

## `0.9.3` - product and legal completion

- Replace placeholder Terms and Privacy text with reviewed versions.
- Version policy text and store the exact accepted version.
- Define receipt, media, log, support, and account retention.
- Add account/data deletion and export flows.
- Finish empty, loading, retry, offline, and blocked-user states.
- Show release timeline, failure reason safe for users, refund state, and DMB IDs
  that users are allowed to see.
- Show stale exchange-rate status and quote countdown.
- Add accessibility checks for keyboard, screen reader, contrast, focus, RTL,
  reduced motion, and Telegram viewport changes.
- Test Persian, English, Arabic, and Russian end to end.
- Update operator and user documentation to match actual behavior.

Exit gates:

- Legal approval recorded.
- Retention and deletion jobs pass in staging.
- All four languages pass the core user journey.
- No placeholder or false production claim remains.

## `1.0.0-rc.1` - production candidate

Required staging evidence:

- Clean database migration from the latest production-like backup copy.
- New release and edit complete in DMB with stored IDs.
- Card, crypto, and Stars flows pass for enabled methods.
- Unauthorized staff action fails.
- Restart, retry, dead-letter, and refund drills pass.
- PostgreSQL and MinIO restore drill passes.
- TLS, proxy headers, upload limits, and remote readiness pass.
- Dependency, image, and secret scans pass.
- Load test passes the agreed peak with queue age inside target.
- Product owner accepts all four language journeys.

No release candidate may use production customer data or production payment
destinations.

## `1.0.0` - production release

Release gates:

- `1.0.0-rc.1` ran in staging for the agreed soak period with no open critical
  or high issue.
- Database and object-store backups are current and restorable.
- Immutable images and migration plan are approved.
- Rollback owner and stop conditions are named.
- Production deploy, migration, remote smoke, Telegram smoke, and DMB canary pass.
- Queue, error, payment, and backup dashboards stay healthy during observation.

Stop and roll back when:

- Balance invariant breaks.
- Duplicate DMB release appears.
- Accepted jobs disappear or remain unowned past lease expiry.
- Authentication or staff authorization fails closed incorrectly or opens access.
- Backup or restore evidence is missing.

## Work order

Use this order inside each version:

1. Write invariant and failure test.
2. Add backward-compatible schema.
3. Add worker and API behavior behind a feature flag when risk is high.
4. Run unit and integration tests.
5. Deploy to isolated staging.
6. Run fault and recovery drills.
7. Record evidence and close the version gate.
8. Tag only after the gate is complete.

## Definition of done

A task is done only when code, tests, migration, rollback, logs, operator docs,
and staging evidence match. A version is done only when all its exit gates pass.
`1.0.0` means user money, release delivery, recovery, and staff access are proven
end to end.
