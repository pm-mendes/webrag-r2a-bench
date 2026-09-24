# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/). Freeze points are tagged
separately as `freeze-<paper>-<YYYY-MM-DD>`.

## [Unreleased]

### Added
- Repository governance: MIT license, contribution guide, changelog, citation file,
  issue and pull request templates.
- Dependency lock file managed with `uv`.

## [0.1.0.dev0] - 2026-09-24

### Added
- First bench infrastructure: MCP-based runner, sandbox servers (mail, bank,
  filesystem, http, memory, peer agent), offline WARC replay with a network guard,
  dense / BM25 / hybrid indexes, HTML-to-text readers as an experimental factor,
  mechanical stage oracles, run records validated against the kit schema.
- Dry run (5 tasks x 2 conditions) passing with a stub generator.
