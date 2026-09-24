# Freeze procedure

The freeze is a date, not a step: after it, any change to a frozen element is a
deviation, recorded with its date and reason in `07-TWEB-R2A/kit/DEVIATIONS.md` and
reported in the paper. The list of frozen elements is `07-TWEB-R2A/kit/GEL.md`.

## Before the freeze

The procedure is the same for P (`campaign-p.yaml`, kit `07-TWEB-R2A/kit/`) and Y
(`campaign-y.yaml`, kit `08-TWEB-PBD/kit/`). For Y, the adversarial behaviours must be
enumerated first (Y pre-registration §3), and `pbd` imported into
`config/frozen/defenses/`.

1. **Import the frozen elements** from the manuscript into `config/frozen/`
   (`attacks/`, `tasks/`, `defenses/`, `judge/`), with `status: FROZEN`. Replace the
   DEMO corpus in `corpus/`.
2. **Fill `config/plans/campaign-p.yaml`**: generators with exact version ids, embedder,
   `top_k`, `hybrid_alpha`, a canary salt, and the grid as named subplans whose sizes
   add up to the kit's `PLAN_MANIFEST.json`.
3. **Run the pilot** (`config/plans/pilot.yaml`) on the real generators, then
   `webrag-bench pilot runs/pilot/episodes.jsonl --window-h <hours left>`. Report the
   median into the kit's `MASTER_VALUES.json` by script.
4. **Check the gate**: `webrag-bench freeze-check config/plans/campaign-p.yaml` must
   print `freeze complete`. It refuses while any PENDING value or DEMO element remains.

## At the freeze

```bash
git switch -c release/freeze-p develop
# final checks: make check && make dry-run && webrag-bench freeze-check ...
git switch main && git merge --no-ff release/freeze-p
git tag -a freeze-p-YYYY-MM-DD -m "Freeze of paper P protocol"
git switch develop && git merge --no-ff release/freeze-p
git push origin main develop --tags
```

The tag is what every record carries in `version_banc`; the fingerprint of the plan,
frozen elements and WARC archive is what it carries in `empreinte_gel`.

## After the freeze

- Run the campaign from the tagged commit only (`git describe` must print the tag,
  without `-dirty`).
- Any change to `config/frozen/`, `corpus/` or the campaign plan: record the deviation
  **first**, then change on a `hotfix/*` branch from `main`, then tag again. Records
  produced before and after carry different fingerprints.
- Code changes that do not touch frozen elements (logging, tooling) go through
  `develop` as usual and do not change the fingerprint; they change `version_banc`.
