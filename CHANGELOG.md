# Changelog

All notable changes are recorded here. Version numbers follow Semantic
Versioning and release states follow `RELEASE_POLICY.md`.

## [Unreleased]

### Planned

- Durable release processing and exact-once refund behavior for `0.8.0`.
- Verified DMB create and edit delivery for `0.9.0`.

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

[Unreleased]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.3...HEAD
[0.8.0-alpha.3]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.2...v0.8.0-alpha.3
[0.8.0-alpha.2]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.1...v0.8.0-alpha.2
[0.8.0-alpha.1]: https://github.com/Ilia-Shakeri/Nitro-Bot/releases/tag/v0.8.0-alpha.1
