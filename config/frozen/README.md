# config/frozen/ — frozen protocol elements

Empty until the freeze. Each subdirectory receives, from the manuscript and the
pre-registration (07-TWEB-R2A/kit/), the corresponding frozen element:

| Directory | Frozen element (kit/GEL.md) | Format |
|---|---|---|
| `attacks/` | exact text of the four families' templates, insertion points, variants | one YAML per family, same schema as `config/demo/attacks/`, `status: FROZEN` |
| `tasks/` | frozen task list, with the open / specified action partition | one YAML per task, same schema as `config/demo/tasks/` |
| `defenses/` | the six conditions, exact configuration and code version (Progent included) | to be defined with the first real defense |
| `judge/` | judge model version id, prompt verbatim, temperature, seed | to be defined |

The SHA-256 fingerprint of these directories, the plan and the WARC archive is
written into every record (`empreinte_gel`). Any change after the freeze changes it
and must be recorded in `07-TWEB-R2A/kit/DEVIATIONS.md`. See `docs/freeze.md`.
