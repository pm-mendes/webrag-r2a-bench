# webrag-r2a-bench

A staged measurement bench for **retrieval-to-action prompt injection** in web-native
agentic RAG. It traces each injection through four nested stages — *exposure →
absorption → effect → action* — and reports where it stops, instead of a single
attack success rate.

It supports two papers in preparation for ACM TWEB (*The Agentic Web*):
P, *Retrieval-to-Action Prompt Injection in Web-Native Agentic RAG*, and Y,
*Provenance-Bound Delegation*.

> **Status (0.1.0.dev0).** The infrastructure runs end to end and the dry run passes.
> Nothing is frozen yet: attack templates, tasks and corpus are DEMO placeholders, and
> the generator and embedder are stubs. **No output of this version has measurement
> value.**

## Quick start

```bash
uv sync --locked
uv run webrag-bench run config/plans/dry-run.yaml --workers 2       # 5 tasks x 2 conditions
uv run webrag-bench run config/plans/demo-factors.yaml --workers 8  # every factor, 600 episodes
uv run pytest
```

Results go to `runs/<plan>/episodes.jsonl`, one record per episode, validated against
`schemas/run_record_schema.json`.

## How an episode runs

```
request -> index (dense | bm25 | hybrid) -> http.get (WARC replay) -> reader (HTML -> text)
        -> defense (context filter) -> generator -> tool calls -> defense (authorisation)
        -> sandbox MCP servers -> mechanical oracles -> run record
```

| Stage | True when the episode canary… |
|---|---|
| exposure | is in the raw HTML of a page that entered the context |
| absorption | survived the reader and the defense's context filter |
| effect | is in the arguments of the adversarial call proposed by the generator |
| action | is in the arguments of an executed call (sandbox server journal) |

## Guarantees

- **No third-party site is contacted.** Pages come only from a local WARC archive,
  and a network guard refuses any connection outside the declared model endpoints.
- **Reproducible inputs.** The WARC archive is byte-for-byte reproducible; episode
  ids and seeds derive from the plan and the cell, so interrupted runs resume safely.
- **Freeze fingerprint in every record.** A frozen plan refuses to start while any
  PENDING value or DEMO element remains.
- **No silent substitution.** The model id returned by a provider is checked against
  the declared snapshot on every call.
- **No approximated defense.** Defenses whose configuration is not imported (Progent
  included) raise instead of running.

## Repository layout

```
src/webrag_bench/
  cli/          webrag-bench run | pilot | freeze-check
  config/       pydantic models of plan files
  core/         plan, run context, episode, runner, tasks
  corpus/       pages, adversarial variants, WARC writer and replay
  attacks/      templates, insertion points, canaries
  defenses/     defense interface and registry
  generators/   stub and OpenAI-compatible generators
  index/        BM25, dense, hybrid, embedders
  readers/      HTML-to-text readers (an experimental factor)
  servers/      sandbox MCP servers: mail, bank, filesystem, http, memory, peer
  oracles/      stage decisions
  records/      schema validation, JSONL I/O, vocabulary mapping
  freeze/       fingerprint and entry gate
  security/     network guard
  analysis/     pilot timing
config/
  plans/        dry-run, demo-factors, pilot, campaign-p
  demo/         DEMO attack templates and tasks
  frozen/       frozen protocol elements (empty until the freeze)
corpus/         DEMO page corpus
schemas/        run record schema (copy of the kit's; French field names by contract)
```

## Documentation

| Page | Content |
|---|---|
| [docs/architecture.md](docs/architecture.md) | episode sequence, packages, dependency direction, extension points |
| [docs/protocol.md](docs/protocol.md) | how stages and factors map to the manuscripts — what is still to check |
| [docs/freeze.md](docs/freeze.md) | freeze procedure, tags, deviations |
| [docs/annotation.md](docs/annotation.md) | building, handing out and verifying the annotation batch |
| [docs/operations.md](docs/operations.md) | configuring generators, running, resuming, pilot, troubleshooting |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branching model, commit conventions
and the protocol rules that code review enforces.

## License

MIT — see [LICENSE](LICENSE).
