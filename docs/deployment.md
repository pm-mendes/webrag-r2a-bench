# Deployment on the OVH machine

> **Not yet tested on the target machine.** The image and compose files were written
> without Docker or a GPU available; validate them on the OVH machine with the pilot
> before relying on them.

## Layout

```
┌──────────────── network "models" (internal: no Internet) ────────────────┐
│  generator  vLLM, 8B model   http://generator:8000/v1                    │
│  embedder   vLLM, embeddings http://embedder:8001/v1                     │
│  bench      webrag-bench     runs/ mounted from the host                 │
└──────────────────────────────────────────────────────────────────────────┘
          + network "egress" only with compose.api.yaml (API generators)
```

Two layers keep third-party sites out of reach: the `models` network has no route to
the Internet, and inside the bench the network guard refuses every host that is not a
declared endpoint.

## Once, on the machine

1. Download the weights into `HF_CACHE` **at the pinned revisions** (the servers run with
   `HF_HUB_OFFLINE=1` and never download at serving time).
2. `cp deploy/.env.example deploy/.env` and fill every value. The image tag, model
   revisions and served model names are part of what the freeze records.
3. Make `runs/` writable by uid 1000 (the bench runs as a non-root user).

## Every campaign

```bash
git checkout <freeze tag>                  # the tag is the bench version
make image                                 # BENCH_VERSION = git describe
docker compose -f deploy/compose.yaml --env-file deploy/.env up -d generator embedder
docker compose -f deploy/compose.yaml --env-file deploy/.env --profile bench \
  run --rm bench run config/plans/campaign-p.yaml --workers 24
```

Declare the local endpoints in the plan with the served names as version ids:

```yaml
embedder: {type: openai-compatible, base_url: "http://embedder:8001/v1", model: "<EMBED_VERSION_ID>"}
generators:
  - {name: G4-8B-OVH, type: openai-compatible, version_id: "<GEN_VERSION_ID>",
     base_url: "http://generator:8000/v1"}
```

vLLM returns the served model name in every response; the bench flags any difference
from `version_id` as `model-substitution`.

## Bench version inside the image

There is no `.git` directory in the image. `make image` passes
`git describe --tags --always --dirty` as the `BENCH_VERSION` build argument, which
becomes `WEBRAG_BENCH_VERSION` and is written into every record. An image built from a
dirty tree carries `-dirty`, and `aggregate --master` refuses its records.

## Monitoring from the host

```bash
uv run webrag-bench status config/plans/campaign-p.yaml --deadline <ISO date-time>
```

It reads `runs/` directly; it does not need the containers.
