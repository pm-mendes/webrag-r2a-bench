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

## Paper Y

```bash
webrag-bench aggregate-y runs/campaign-y --policy pbd --partial-fault-rate <rate>
webrag-bench aggregate-y runs/campaign-y --policy pbd --partial-fault-rate <rate> \
  --master <08 kit>/MASTER_VALUES.json
```

| Key of the 08 MASTER_VALUES | Computed from |
|---|---|
| `cout_delegation.surcout_latence_ms_median` / `_p99` | signing + verification time per signed episode without failure |
| `cout_delegation.surcout_taille_message_octets` | median attestation bytes per signed episode without failure |
| `degradation_gracieuse.utilite_sans_provenance` | utility, provenance off, no defense |
| `degradation_gracieuse.utilite_avec_provenance` | utility, provenance on, the policy, no failure |
| `degradation_gracieuse.utilite_sous_defaillance_partielle` | same, at `--partial-fault-rate` |
| `egalite_inter_episodes.*` | clean/attacked pairs, provenance on, the policy, no failure |

Not written: `borne_formelle_predite` (from the formal core) and `ecart_mesure_borne`
(computed once the bounds exist).

**Latency overhead is measured on the cryptographic work itself.** The end-to-end
duration difference of off/on pairs is kept in the fragment's `_provenance` as a
secondary figure: in the dry run it comes out negative (-4 ms against about 1 ms of
signing and verification), because scheduling and model latency noise dominate it.
Which of the two the irreducible-cost bound speaks about is **to check** against the
manuscript.

## Strict merge

`--master` only replaces keys the master file already declares; an undeclared section
or key is refused. The kit decides which values the manuscript uses.
