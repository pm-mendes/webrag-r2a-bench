# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/). Freeze points are tagged
separately as `freeze-<paper>-<YYYY-MM-DD>`.

## [Unreleased]

### Added
- Aggregation into the kit's MASTER_VALUES format (`webrag-bench aggregate`, and
  `pilot --master`): funnel counts per cell with n_X / n_E as the end-to-end rate,
  reader factor, per-defense stage counts, WARC fingerprint. Refuses to write numbers
  from stub, unfrozen, mixed or untagged runs.
- Episode transcripts (`transcripts.jsonl`): what the generator saw and proposed,
  stored beside the run records (outside the schema).
- Annotation batch builder: stratified, blinded, deterministic, frozen by SHA-256
  (`webrag-bench annotation build | verify`), with a DEMO batch and the P skeleton.
- Repository governance: MIT license, contribution guide, changelog, citation file,
  issue and pull request templates.
- Dependency lock file managed with `uv`.
- `webrag-bench` CLI with `run`, `pilot` and `freeze-check` subcommands.
- Pydantic validation of plan, task, template and corpus files.
- Pilot plans are refused while a generator is left PENDING.
- Quality tooling: ruff (lint and format), strict mypy, coverage, pre-commit hooks,
  `Makefile` targets, and a GitHub Actions workflow (lint, types, tests on 3.12 and
  3.13, dry run, campaign plan refusal).
- Tests for the OpenAI-compatible client (model substitution detection, tool name
  mapping), the three indexes, and resuming an interrupted plan.

- Technical documentation: architecture, protocol mapping, freeze procedure,
  operations.

### Changed
- Code, identifiers, configuration, demo data and documentation are now in English.
  The run record schema keeps its French field names (contract with the kit).
- Package split into subpackages (`core`, `corpus`, `attacks`, `defenses`,
  `generators`, `index`, `readers`, `servers`, `oracles`, `records`, `freeze`,
  `security`, `analysis`, `cli`, `config`).
- Plans declare their grid as named `subplans`; `config/gel/` is now `config/frozen/`.
- Tests split into `tests/unit/` and `tests/integration/`.
- Exceptions renamed with an `Error` suffix (`ForbiddenConnectionError`,
  `NotInCorpusError`, `UnspecifiedDefenseError`, `IncompleteFreezeError`).

## [0.1.0.dev0] - 2026-09-24

### Added
- First bench infrastructure: MCP-based runner, sandbox servers (mail, bank,
  filesystem, http, memory, peer agent), offline WARC replay with a network guard,
  dense / BM25 / hybrid indexes, HTML-to-text readers as an experimental factor,
  mechanical stage oracles, run records validated against the kit schema.
- Dry run (5 tasks x 2 conditions) passing with a stub generator.
