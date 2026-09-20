# Changelog

All notable changes are recorded here. Version numbers follow Semantic
Versioning and release states follow `RELEASE_POLICY.md`.

## [Unreleased]

### Planned

- Durable release processing and exact-once refund behavior for `0.8.0`.
- Verified DMB create and edit delivery for `0.9.0`.

## [0.9.0-alpha.7] - 2026-09-20

### Added

- Atomic pre-submit checkpoint with release ID, title, EAN, ISRC, time, and stable fingerprint.
- Stored DMB submission fingerprint for crash and duplicate review.

### Fixed

- Successful DMB evidence must match the exact codes captured before Save.
- Uncertain jobs preserve searchable codes for manual remote-record review.
- Approved retry clears stale submission evidence before a new attempt.

### Not run

- Final DMB Save and publication were not used.

## [0.9.0-alpha.6] - 2026-09-20

### Added

- Immutable balance ledger for top-ups, release charges, refunds, and referral rewards.
- Staff audit records for payment decisions and support replies.
- Durable notification outbox for admin claims and user results.
- Idempotency keys and receipt fingerprints for manual payment claims.

### Fixed

- Payment and support actions now require the configured manager, group, and topic.
- Crypto claims now persist receipt evidence and validate their quote before upload.
- Manual crypto claims now require proof and reject reused receipt images.
- Processed payment buttons are removed after a decision.

## [0.9.0-alpha.5] - 2026-09-13

### Fixed

- Unknown contributors now leave the lookup with Tab because Escape closes the full create layer.
- Contributor roles now use the real multi-select and verify Performer is the only selected role.
- Track upload now targets the file input directly instead of opening a native file chooser first.

## [0.9.0-alpha.4] - 2026-09-13

### Fixed

- Live navigation now targets Audio, Create audio product, and the real album-create iframe.
- DMB dates convert from stored ISO form to the live `DD.MM.YYYY` form without submitting on Enter.
- Label selection uses the live select field.
- Genre, label lookup, and known-contributor results require an exact match instead of the first suggestion.
- Contributors are explicitly applied to tracks.
- Digital 45 uses the live DMB option value `14`.

## [0.9.0-alpha.3] - 2026-09-13

### Added

- Exact DMB genre and subgenre choices in the mini-app, with safe normalization of older saved choices.
- Explicit per-artist DMB contributor-account state through form, API contract, notice, and worker job.
- CI checks for backend, frontend, DMB contract, Robot dry-run, and DMB container build.

### Fixed

- iTunes Digital 45 uses DMB's live select value `14`.
- Edit orders fail before validation, file staging, and charging while DMB edit delivery is disabled.
- Edit controls and route stay hidden while the edit feature flag is disabled.
- DMB image now receives the shared genre catalog from the root build context.

### Known gaps

- Authenticated wizard selectors and the final Save still need a controlled DMB staging submission.
- DMB edit delivery remains disabled until its distinct browser flow passes staging.

## [0.9.0-alpha.2] - 2026-09-13

### Added

- Exact DMB create-wizard contract for Label, dates, price codes, contributors, tracks, territories, platforms, review, and final Save.
- Explicit DMB mapping for every genre and subgenre currently offered by the mini-app.
- Exact 3000x3000 JPEG cover preparation and WAV signature validation.
- Persistent circuit breaker for repeated failures and uncertain final submissions.
- Full worker success, retry, uncertain, circuit, media, and wizard contract tests.

### Fixed

- Re-releases now use the original release year for the C line and the current year for the P line.
- New contributors keep only the Performer role; known contributors must resolve from DMB search.
- Track upload now starts through Add Tracks and delivery selects Worldwide plus all platforms.
- Final review checks user data before Save.
- Completion evidence now requires a real PNG screenshot, not only an existing file path.
- Fixed sleeps were removed from the album page workflow.

### Known gaps

- Authenticated wizard selectors and final Save still need a controlled DMB staging submission.
- No public direct API contract was found; Kontor says direct database interfaces are available upon request.
- The DMB edit workflow remains disabled.
- Container build proof is unavailable on this workstation.

## [0.9.0-alpha.1] - 2026-09-13

### Added

- Isolated DMB job files carrying the full release contract.
- Atomic DMB claims with worker leases, heartbeats, bounded attempts, and crash recovery.
- Stored DMB release ID, EAN/UPC, ISRC list, submission times, and evidence path.
- Manual review state and audited complete, retry, or fail resolution.
- Contract tests and a Robot dry-run fixture.

### Fixed

- The browser flow now clicks final Save before a release can complete.
- A completed callback now requires validated codes and local screenshot evidence from the allowed DMB host.
- Failures after Save begins stop in manual verification instead of risking a duplicate album.
- Edit orders cannot be charged until their source release has a stored DMB ID.
- The live worker no longer shares one mutable SQLite metadata row.

### Known gaps

- DMB selectors and success evidence still need real staging validation with authorized credentials.
- Producer roles, artist roles, profile mappings, re-release details, subgenre, and explicit metadata are carried but not all are entered in the browser form yet.
- Edit delivery remains disabled until a distinct edit flow passes staging without duplicate creation.
- Migration `014` still needs a PostgreSQL staging run against production-like data.
- Earlier `0.8.0` money, notice, payment quote, concurrency, and orphan-retention gates remain open.

## [0.8.0-alpha.3] - 2026-09-13

### Added

- Hard chunked read limits for audio and cover uploads.
- Shared genre and subgenre catalog enforced in both clients and server.
- Database constraints for credit, release cost, job attempts, and state values.
- Strict Spotify and Apple Music artist URL validation.

### Fixed

- Unsafe submission identifiers can no longer enter object-storage paths.
- Oversized metadata lists and values are rejected before persistence.
- Frontend validation now matches server genre, URL, email, and length rules.

### Known gaps

- Migration `013` still needs a PostgreSQL staging run against production-like data.
- Object upload is memory-bounded but conversion still needs the accepted file in memory.
- Orphan-object retention and payment quote upload ordering remain open.

## [0.8.0-alpha.2] - 2026-09-12

### Added

- Durable database release jobs with leases, retries, and a dead state.
- Restart recovery for legacy staging releases.
- Durable notification phase after media conversion.
- Additive release-job migration and failure reason storage.

### Fixed

- Terminal processing failure now refunds credits exactly once.
- Release charge and job creation now commit together.
- Future-dated signed login payloads are rejected.
- Staged uploads are removed when database work fails.

### Known gaps

- PostgreSQL crash and concurrency drills still need an isolated test stack.
- A worker crash after remote notice acceptance can still repeat that notice.
- Input streaming, strict metadata validation, and orphan retention remain open.
- DMB final submission and real edit delivery are not proven.

## [0.8.0-alpha.1] - 2026-09-12

### Added

- Canonical repository `VERSION`.
- Versioned roadmap from the audited baseline through `1.0.0`.
- Release, tag, migration, evidence, and rollback policy.

### Changed

- Runtime and frontend build versions now use `0.8.0-alpha.1`.
- README now describes the current build as pre-release.
- Deployment text now states that the Caddy gateway network is external.

### Known gaps

- DMB final submission and edit delivery are not proven.
- Release jobs and Telegram notifications are not durable.
- Staff actions need actor authorization and audit records.
- Manual crypto claims need payment proof.
- Full staging, backup/restore, and production gates remain open.

[Unreleased]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.7...HEAD
[0.9.0-alpha.7]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.6...v0.9.0-alpha.7
[0.9.0-alpha.6]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.5...v0.9.0-alpha.6
[0.9.0-alpha.5]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.4...v0.9.0-alpha.5
[0.9.0-alpha.4]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.3...v0.9.0-alpha.4
[0.9.0-alpha.3]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.2...v0.9.0-alpha.3
[0.9.0-alpha.2]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.1...v0.9.0-alpha.2
[0.9.0-alpha.1]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.3...v0.9.0-alpha.1
[0.8.0-alpha.3]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.2...v0.8.0-alpha.3
[0.8.0-alpha.2]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.1...v0.8.0-alpha.2
[0.8.0-alpha.1]: https://github.com/Ilia-Shakeri/Nitro-Bot/releases/tag/v0.8.0-alpha.1
