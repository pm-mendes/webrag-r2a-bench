# Annotation batch

The pre-registration (kit, section 7) fixes the rules: two independent annotators see
**the same** batch, blind to condition, generator and family; a third person
arbitrates disagreements; Pedro builds, stratifies and freezes the batch, and neither
annotates nor edits it afterwards. The partition and the sampling fractions are fixed
**before** annotation.

## Building

1. Write the batch configuration (`config/annotation/`). The P skeleton is
   `batch-p.yaml`; it is refused while a PENDING value remains.

   ```yaml
   name: batch-p
   status: FROZEN
   source_run: campaign-p          # runs/campaign-p/
   seed: <drawn at the freeze>
   strata: [family, defense_on]    # keys: family, defense, defense_on, generator,
                                   #       index, reader, action_type, task
   allocation: {per_stratum: 30}   # or {fraction: 0.004}
   max_items: 240                  # calendar ceiling; exceeding it is an error
   exclude_stub_episodes: true
   question: <from the frozen judge protocol>
   labels: [...]
   ```

2. `webrag-bench annotation build config/annotation/batch-p.yaml`

The batch lands in `runs/<source_run>/annotation/<name>/`. Episodes with a nesting
violation are never eligible (analysis plan, section 2). A stratum with fewer episodes
than requested is drawn in full and its **shortfall** is written in the manifest. An
allocation above `max_items` is refused: the batch is never silently truncated.

## Handing out

| Give to each annotator | Keep sealed | For the paper |
|---|---|---|
| `items.jsonl`, `sheet.csv`, `instructions.md` | `key.jsonl` | `manifest.json` |

Each annotator fills a **copy** of `sheet.csv` named after them and hands it back; the
filled sheets are stored outside the batch directory.

## Integrity

`webrag-bench annotation verify runs/<run>/annotation/<name>` recomputes the SHA-256 of
every file against the manifest and reports any change or extra file. A built batch is
never rebuilt: building a batch whose directory exists fails.

## Determinism

Each stratum is drawn with its own generator seeded by (seed, stratum): adding a
stratum does not change the draw of the others. Item ids are derived from (seed,
episode) and the item order is shuffled with the seed. The same configuration on the
same run yields byte-identical `items.jsonl` and `key.jsonl`.
