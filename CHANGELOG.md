# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/). Freeze points are tagged
separately as `freeze-<paper>-<YYYY-MM-DD>`.

## [Unreleased]

### Added
- Defense interface: `authorize(call, task, context)` with a `DecisionContext`
  carrying per-page signed provenance; `requires_provenance` flag. DEMO policy
  `provenance-demo` (not the mechanism of paper Y); `pbd` registered as pending.
  The Y dry run gains a policy subplan.
- Paper Y: inter-episode equality. Measures record the cell and an `effects_digest`;
  `analysis.equality` pairs clean and attacked episodes of the same fixed plan and
  reports equal pairs and violations (operationalisation to check).
- Utility oracle: tasks may declare a `benign_goal`; `measures.utility` says whether it
  was executed (undefined for answer-only tasks). The stub generator makes the benign
  call first so that the oracle is exercised in dry runs. Demo tasks declare goals.
- Paper Y: partial failure of signing parties. `fault_rates` factor and plan-level
  `fault_mode` (`missing`, `corrupt`, `unknown-key`); failing parties drawn from the
  episode seed and recorded in `measures.provenance.faulty_parties`.
- Paper Y: delegation cost per episode (`measures.provenance.cost`): signing and
  verification time, number of attestations, bytes added to messages. Peer answers
  are verified too (`unverified-attestation` otherwise).
- Paper Y: `provenance: [off, on]` factor. With `on`, pages and the peer agent are
  served by signing servers and the agent verifies each attestation; results go to a
  new `measures.jsonl` beside the records. `y-dry-run` plan. P episode ids unchanged.
- Signed cross-party provenance for paper Y (first block): deterministic Ed25519 party
  keys, attestations with derivation chains, verification, PROV-O JSON-LD export,
  transport in MCP result `_meta`, signing http and peer servers. Not wired into
  episodes yet.
- Deployment for the OVH machine: bench Docker image (`make image`), compose file with
  vLLM generator and embedder on an internal network, API egress override,
  `.env.example`. Not yet tested on the target machine.
- `WEBRAG_BENCH_VERSION` overrides the git-derived bench version (set at image build).
- Campaign monitoring (`webrag-bench status`): progress, measured throughput over the
  last hour, projected end against a deadline, anomalies (model substitution, tool
  errors, failures), and a Markdown checkpoint report.
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
