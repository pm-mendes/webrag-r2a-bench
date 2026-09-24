# Architecture

## One episode

```
                    ┌─────────────── RunContext (one per worker) ───────────────┐
                    │ plan · WARC replay · embedder · index cache (family,      │
                    │ reader, index) · freeze fingerprint · bench version       │
                    └───────────────────────────────────────────────────────────┘
Cell ──► index.search(request, top_k)
     ──► http.get(url)            MCP call, served by WarcReplay (never the network)
     ──► reader(html)             HTML -> text; the reader is an experimental factor
     ──► defense.filter_context
     ──► generator.generate       stub | OpenAI-compatible endpoint
     ──► for each proposed call:
            defense.authorize ──► refused: recorded with bloque_par
                              └─► allowed: MCP call to the sandbox server, effect journaled
     ──► decide_stages            canary in: html (exposure) · text (absorption)
                                             · proposed call (effect) · journal (action)
     ──► run record               validated against schemas/run_record_schema.json
```

`core/episode.py` implements this sequence; everything else is a component it calls.

## Packages

| Package | Responsibility | Notes |
|---|---|---|
| `cli` | `webrag-bench run \| pilot \| freeze-check` | thin; no logic |
| `config` | pydantic models of plan files | a malformed plan fails before the first episode |
| `core.plan` | cells, episode ids and seeds | ids derive from (plan, cell): resuming is safe |
| `core.context` | per-worker state and index cache | one index per (family, reader, index) |
| `core.episode` | the sequence above | single turn |
| `core.runner` | archive build, fingerprint, worker pool, JSONL output | `spawn` workers; one failing episode never kills a worker |
| `core.tasks` | task files | the adversarial goal must carry `{canary}` |
| `corpus` | benign pages, adversarial variants, WARC write/replay | adversarial pages are precomputed into the archive |
| `attacks` | templates, insertion points, canaries | |
| `defenses` | interface, registry | unspecified defenses raise |
| `generators` | stub, OpenAI-compatible, registry | model id checked on every call |
| `index` | BM25, dense, hybrid, embedders | adapted from the WI-IAT code base |
| `readers` | four HTML-to-text readers | each recorded with its library version |
| `servers` | six sandbox MCP servers and the effect journal | fresh servers per episode |
| `oracles` | stage decisions and nesting check | nesting is checked, never forced |
| `records` | schema validation, JSONL I/O, vocabulary mapping | schema field names stay French |
| `freeze` | fingerprint, entry gate | |
| `security` | network guard | installed in every worker |
| `analysis` | pilot timing, aggregation into MASTER_VALUES, campaign monitoring | |
| `annotation` | annotation batch build and verification | see docs/annotation.md |
| `provenance` | Ed25519 attestations, chains, PROV-O, MCP transport | paper Y; see docs/provenance.md |

## Dependency direction

```
cli ─► core ─► {corpus, attacks, defenses, generators, index, readers, servers,
                oracles, records, freeze, security} ─► config
```

Lower packages never import `core.episode`, `core.runner` or `cli`. `core/__init__.py`
re-exports nothing, to keep imports acyclic (`corpus` and `defenses` use `core.tasks`).

## Adding a component

| To add… | Do |
|---|---|
| a reader | a function `str -> str` in `readers/`, registered in `readers/registry.py` with its package |
| a defense | a `Defense` subclass in `defenses/`, registered in `defenses/registry.py`; remove it from `PENDING_DEFENSES`. `authorize(call, task, context)` receives a `DecisionContext` (signed provenance of each page); set `requires_provenance = True` if it needs it. The Y mechanism goes here as `pbd` |
| a generator type | a class following `generators.base.Generator`, a `type` value in `config/models.py`, a branch in `generators/registry.py` |
| a sandbox server | a module in `servers/` returning an `MCPServer`, registered in `servers/__init__.py`; add its effectful tools to `EFFECTFUL_TOOLS` |

Each addition comes with unit tests, and with an update of `docs/protocol.md` if it
changes what a stage means.
