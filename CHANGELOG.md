# Changelog

All notable changes are recorded here. Version numbers follow Semantic
Versioning and release states follow `RELEASE_POLICY.md`.

## [Unreleased]

### Planned

- Durable release processing and exact-once refund behavior for `0.8.0`.
- Verified DMB create and edit delivery for `0.9.0`.

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

[Unreleased]: https://github.com/Ilia-Shakeri/Nitro-Bot/compare/v0.8.0-alpha.1...HEAD
[0.8.0-alpha.1]: https://github.com/Ilia-Shakeri/Nitro-Bot/releases/tag/v0.8.0-alpha.1
