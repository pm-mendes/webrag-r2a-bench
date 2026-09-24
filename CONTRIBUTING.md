# Contributing

## Setup

```bash
uv sync --locked          # creates .venv from uv.lock, dev tools included
make check                # lint + types + tests
make dry-run              # 5 tasks x 2 conditions, stub generator
```

`uv.lock` is the source of truth for dependency versions. Change dependencies with
`uv add` / `uv remove` only, and commit the updated lock file in the same commit.

## Branches

| Branch | Purpose | Merges into |
|---|---|---|
| `main` | Stable. Every tag lives here (releases, freeze points). | — |
| `develop` | Integration. All work lands here first. | `main`, via `release/*` |
| `feature/<topic>` | One topic per branch, branched from `develop`. | `develop` |
| `fix/<topic>` | Bug fix, branched from `develop`. | `develop` |
| `release/<version>` | Stabilisation before a tag (freeze, submission). | `main` and `develop` |
| `hotfix/<topic>` | Urgent fix on a tagged version, branched from `main`. | `main` and `develop` |

Every merge into `develop` or `main` goes through a pull request with a green CI.
Merges use `--no-ff` so that each topic stays visible in the history.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), in English:

```
<type>(<scope>): <imperative summary, lower case, no period>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`.
Scopes follow the package layout: `core`, `corpus`, `attacks`, `defenses`,
`generators`, `index`, `readers`, `servers`, `oracles`, `records`, `freeze`, `cli`,
`provenance`.

## Tags

- `vX.Y.Z` — software releases.
- `freeze-<paper>-<YYYY-MM-DD>` — a protocol freeze point (`paper` is `p` or `y`).
  The tag is what records carry in `version_banc`.

## Protocol rules

These rules come from the pre-registration of the papers and are not negotiable in
code review.

1. **No third-party site is ever contacted.** Pages come from the WARC archive only;
   the network guard must stay installed in every worker.
2. **Nothing is frozen in this repository by hand.** Frozen elements (attack
   templates, defenses, task list, judge, corpus, analysis constants) come from the
   manuscript kit into `config/frozen/`. After the freeze tag, any change to them is a
   deviation and must be recorded in `07-TWEB-R2A/kit/DEVIATIONS.md` before merging.
3. **No silent substitution.** A generator is declared with an exact version id; a
   provider that answers with another model id marks the episode.
4. **The run record schema belongs to the kit.** `schemas/run_record_schema.json` is a
   byte-for-byte copy of `07-TWEB-R2A/kit/schemas/run_record_schema.json`; a test
   enforces it. Its field names are French by contract with the manuscripts: do not
   translate them.
5. **Stub components never produce a reported number.** The stub generator and stub
   embedder flag every episode they touch.
