# Aggregation into the kit

Step 2 of the analysis plan (`07-TWEB-R2A/kit/PLAN-ANALYSE.md`): run records ->
per-cell counts -> `MASTER_VALUES.json` -> `valeurs.tex` -> manuscript via `\mv{key}`.
The bench implements the first arrow; the kit's `generer_valeurs.py` does the rest.

```bash
webrag-bench aggregate runs/campaign-p                       # writes master_values_fragment.json
webrag-bench aggregate runs/campaign-p --master <kit>/MASTER_VALUES.json
webrag-bench pilot runs/pilot/episodes.jsonl --window-h 72 --master <kit>/MASTER_VALUES.json
```

## What is written

| Section of MASTER_VALUES | Content | Source |
|---|---|---|
| `entonnoir.cellules` | per cell (default: family x defense): `N, n_E, n_A, n_F, n_X`, the three conditionals, `taux_action_bout_en_bout = n_X / n_E` | attacked episodes |
| `effets_defense.entrees` | per defense: stage counts | attacked episodes |
| `facteur_lecteur.entrees` | per family x reader: `N, n_E, n_A, p_A_sachant_E` | attacked episodes |
| `reproductibilite.empreinte_corpus_warc` | SHA-256 of the replayed archive | `freeze.json` |
| `pilote.*` | median, quartiles, count, date, feasibility verdict | pilot run |

Only these keys are replaced; every other key and comment of the file is kept.

## What is not computed

Intervals, effect estimands, multiplicity corrections and the degenerate-cell rule
depend on constants that are still PENDING in the analysis plan. They are added when
the plan is frozen, not before.

## Rules applied

- Episodes with a nesting violation are excluded and counted (analysis plan, section 2).
- Unattacked episodes (`aucune`) are left out of the funnels: no stage can be reached
  without an attack.
- A conditional with a zero denominator is `null`, so `generer_valeurs.py` leaves it
  red in the PDF; the reporting rule applies.
- **Nothing reaches `MASTER_VALUES.json` from a run that used a stub component, is not
  frozen, mixes fingerprints, or comes from an untagged or dirty bench version.** The
  pilot section only requires real generators.

A test feeds the produced cells to the kit's own `verifier_entonnoir.py`.
