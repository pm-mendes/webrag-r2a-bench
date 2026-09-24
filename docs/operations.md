# Operations

## Configuring generators

Keys never go in the repository. Each generator names the environment variable that
holds its key (`key_env`). Export them in the shell; a `.env` file (ignored by git) can
be loaded with `set -a; source .env; set +a`. The bench does not read `.env` itself.

```yaml
generators:
  - {name: G1, type: openai-compatible, version_id: "<exact snapshot id>",
     base_url: "https://api.provider.example/v1", key_env: WEBRAG_KEY_G1}
  - {name: G4-8B-OVH, type: openai-compatible, version_id: "<model id served by vLLM>",
     base_url: "http://<ovh-host>:8000/v1"}
```

The host of every `base_url` is added to the network guard's allowlist; nothing else
is reachable. If a provider answers with another model id, each affected episode
carries `model-substitution: declared=… returned=…` in `erreurs`. Do not work around
it: record the deviation.

## Running

```bash
uv run webrag-bench run <plan> --workers 24
uv run webrag-bench run <plan> --workers 24 --limit 100    # first 100 pending cells
```

| File in `runs/<plan>/` | Content |
|---|---|
| `episodes.jsonl` | one validated record per episode |
| `failures.jsonl` | episodes that raised, with the cell and the error |
| `freeze.json` | fingerprint, WARC SHA-256, bench version |
| `corpus.warc` | the archive the run replayed |

**Resuming**: rerun the same command. Episode ids are deterministic and completed
episodes are skipped. Failed episodes are retried, since they are not in
`episodes.jsonl`.

On a remote machine, run inside `tmux` or `nohup` so that a dropped SSH session does
not stop the campaign.

## Pilot

```bash
uv run webrag-bench run config/plans/pilot.yaml --workers 24
uv run webrag-bench pilot runs/pilot/episodes.jsonl --window-h <hours left> --workers 24
```

The output gives the median per generator and overall, and whether P, Y, and P+Y on a
shared machine fit the remaining window. If they do not, the fallback rule of the
pre-registration applies, in its declared order.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `ForbiddenConnectionError` | code tried to reach a host outside the allowlist; check `base_url` |
| `pilot refused: unresolved elements` | a generator or the embedder is still PENDING in the plan |
| `campaign refused: unresolved elements` | the freeze is incomplete; the message lists the files |
| `UnspecifiedDefenseError` | the plan uses a defense whose configuration is not imported |
| `stub-component` in `erreurs` | a stub generator or embedder was used; the episode is not a measurement |
