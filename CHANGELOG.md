# Changelog

All notable changes are recorded here. Version numbers follow Semantic
Versioning and release states follow `RELEASE_POLICY.md`.

## [Unreleased]

### Planned

- Durable release processing and exact-once refund behavior for `0.8.0`.
- Verified DMB create and edit delivery for `0.9.0`.

## [0.9.0-alpha.27] - 2026-10-04

### Fixed

- DMB Next buttons now activate through their DOM event after readiness proof,
  avoiding Firefox iframe coordinates outside the headless viewport.

### Deployment

- The fourteenth live no-save preflight restored frame context and found the
  real Next button, then exposed headless scrolling outside the viewport.

## [0.9.0-alpha.26] - 2026-10-04

### Fixed

- The create flow now re-enters the live album iframe after contributor
  addition refreshes it and returns browser focus to the outer application.

### Deployment

- The thirteenth live no-save preflight proved contributor addition resets
  frame context; the visible album form remained inside the refreshed iframe.

## [0.9.0-alpha.25] - 2026-10-04

### Added

- The filled album form DOM is retained before navigation so live controls can
  be diagnosed even when a failed wait returns browser focus to the shell.

### Deployment

- The twelfth live no-save preflight reproduced the missing legacy Next button
  and proved teardown-time source capture is too late for the active form.

## [0.9.0-alpha.24] - 2026-10-04

### Fixed

- Failure evidence now reads the active iframe document directly instead of
  storing only the outer DMB application shell.

### Deployment

- The eleventh live no-save preflight passed contributor handling, then found
  no legacy Next button; prior page-source evidence hid the active frame DOM.

## [0.9.0-alpha.23] - 2026-10-04

### Fixed

- The create flow no longer waits for the removed `contributors2tracks`
  checkbox; the live form carries album contributors into the next step.

### Deployment

- The tenth live no-save preflight proved exact Performer selection, then
  exposed the removed legacy contributor checkbox.

## [0.9.0-alpha.22] - 2026-10-04

### Fixed

- Contributor role selection now updates the hidden Select2 source and emits
  its change event instead of clicking inaccessible option elements.

### Deployment

- The ninth live no-save preflight passed dates and prices, then exposed the
  hidden contributor-role select interaction.

## [0.9.0-alpha.21] - 2026-10-04

### Fixed

- DMB date entry now dismisses the live date picker after value proof so it
  cannot intercept the following price selection.

### Deployment

- The eighth live no-save preflight accepted both normalized dates, then
  exposed the still-open date picker over the price field.

## [0.9.0-alpha.20] - 2026-10-04

### Fixed

- DMB date proof now compares normalized digits because the live masked input
  stores `DDMMYYYY` while it displays `DD.MM.YYYY`.

### Deployment

- The seventh live no-save preflight passed login, collapsed navigation,
  product type, media, title, language, and genre before exposing the harmless
  masked-date value mismatch.

## [0.9.0-alpha.19] - 2026-10-04

### Fixed

- DMB custom completion fields now commit the highlighted live suggestion with
  keyboard selection when the legacy result table is absent.
- Final page source is retained with failure evidence for exact live DOM
  diagnosis without enabling Save.

### Deployment

- The sixth live no-save preflight passed collapsed navigation, then proved
  that genre text must be committed as a real suggestion.

## [0.9.0-alpha.18] - 2026-10-04

### Fixed

- DMB Audio navigation now finds the menu in both expanded and collapsed
  sidebar states and activates it through its DOM event.

### Deployment

- The fifth live no-save preflight logged in successfully, then exposed the
  hidden Audio label while the dashboard sidebar was collapsed.

## [0.9.0-alpha.17] - 2026-10-04

### Fixed

- Live DMB text completion now clicks an exact suggestion when it appears and
  otherwise confirms the already accepted field value by blurring the input.

### Deployment

- The fourth live no-save preflight passed login, product type, EAN, cover,
  title, and language before exposing the genre suggestion mismatch.

## [0.9.0-alpha.16] - 2026-10-03

### Fixed

- DMB login now uses the password-masking Selenium keyword so credentials do
  not appear in Robot execution logs.
- Cover upload now waits for the filename shown by the live custom upload
  control instead of reading the browser-cleared hidden file input.

### Security

- Existing DMB preflight HTML and XML logs on the test VPS were sanitized and
  verified to contain no remaining password value.

## [0.9.0-alpha.15] - 2026-10-03

### Fixed

- Product-type selection now targets the visible `(Maxi-) Single` card instead
  of the hidden select option with the same text.

### Deployment

- The second live no-save preflight passed login and navigation, then stopped
  safely on the hidden duplicate before any release was claimed or saved.

## [0.9.0-alpha.14] - 2026-10-03

### Fixed

- Headless DMB navigation now opens Create audio product from the visible fixed
  submenu without relying on native scroll-to-click behavior.

### Deployment

- The first live no-save preflight proved login and exposed this navigation
  mismatch before any release was claimed or saved.

## [0.9.0-alpha.13] - 2026-10-03

### Added

- Read-only, worker-authenticated lookup for one explicit DMB preflight release.
- Create preflight runner that downloads and validates media, fills the DMB form,
  captures review evidence, and cannot run the Save keyword.

### Security

- Preflight does not claim the queue, mutate release status, write a submission
  checkpoint, or receive the separate manual-review secret.

## [0.9.0-alpha.12] - 2026-10-03

### Fixed

- DMB dry-run standby now stays alive when all delivery gates are disabled.
- Dry-run still rejects any enabled create or edit delivery gate, so it cannot
  claim live jobs.

### Deployment

- The VPS worker can now expose health checks without opening the DMB site or
  saving and publishing a release.

## [0.9.0-alpha.11] - 2026-10-03

### Fixed

- Financial ledger migration backfill keys now avoid SQLAlchemy bind parsing
  for literal colons.
- Added regression checks for top-up, charge, and refund migration keys.

### Deployment

- The failed migration stayed transactional and the production database
  remained at revision `011` before this fix.

## [0.9.0-alpha.10] - 2026-10-03

### Fixed

- The backend image now installs the SQLAlchemy asyncio runtime dependency so
  Alembic migrations can run during VPS deployment.
- Added a regression check for the backend migration dependency contract.

### Deployment

- This hotfix was found before schema mutation; the database stayed at revision
  `011` until the corrected image was built.

## [0.9.0-alpha.9] - 2026-09-20

### Added

- Native headless Firefox delivery for unattended Linux VPS operation.
- Internal worker live and ready endpoints with poll, busy-job, and circuit state.
- Multi-architecture driver install with pinned checksums.
- VPS rollout and official-interface migration runbook.

### Changed

- Removed the Xvfb runtime dependency.
- Compose now gives the worker health checks, init, shared memory, and graceful stop time.
- CI now validates both Robot suites and the Compose file.

### Not run

- The container image was not built on this host because Docker is unavailable.
- Final DMB Save and Publish were not used.

## [0.9.0-alpha.8] - 2026-09-20

### Added

- Distinct DMB edit suite for exact source album and single-track metadata.
- Separate edit submit gate for track Save, album Save, and Publish.
- Source EAN/ISRC binding and immutable field-level edit audit diff.

### Fixed

- Edit polling now runs only when its worker gate is explicitly enabled.
- Missing source evidence and unsupported audio replacement fail before delivery.
- Unchanged covers are no longer uploaded again.

### Not run

- Final DMB Save and Publish were not used.

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

[Unreleased]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.27...HEAD
[0.9.0-alpha.27]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.26...v0.9.0-alpha.27
[0.9.0-alpha.26]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.25...v0.9.0-alpha.26
[0.9.0-alpha.25]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.24...v0.9.0-alpha.25
[0.9.0-alpha.24]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.23...v0.9.0-alpha.24
[0.9.0-alpha.23]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.22...v0.9.0-alpha.23
[0.9.0-alpha.22]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.21...v0.9.0-alpha.22
[0.9.0-alpha.21]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.20...v0.9.0-alpha.21
[0.9.0-alpha.20]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.19...v0.9.0-alpha.20
[0.9.0-alpha.19]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.18...v0.9.0-alpha.19
[0.9.0-alpha.18]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.17...v0.9.0-alpha.18
[0.9.0-alpha.17]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.16...v0.9.0-alpha.17
[0.9.0-alpha.16]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.15...v0.9.0-alpha.16
[0.9.0-alpha.15]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.14...v0.9.0-alpha.15
[0.9.0-alpha.14]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.13...v0.9.0-alpha.14
[0.9.0-alpha.13]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.12...v0.9.0-alpha.13
[0.9.0-alpha.12]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.11...v0.9.0-alpha.12
[0.9.0-alpha.11]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.10...v0.9.0-alpha.11
[0.9.0-alpha.10]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.9...v0.9.0-alpha.10
[0.9.0-alpha.9]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.8...v0.9.0-alpha.9
[0.9.0-alpha.8]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.9.0-alpha.7...v0.9.0-alpha.8
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
