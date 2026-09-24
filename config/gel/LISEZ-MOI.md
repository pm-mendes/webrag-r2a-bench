# config/gel/ — éléments gelés

Vide tant que le gel n'a pas eu lieu. Chaque sous-dossier reçoit, depuis le manuscrit
et le pré-enregistrement (07-TWEB-R2A/kit/), l'élément gelé correspondant :

| Dossier | Élément gelé (kit/GEL.md) | Source |
|---|---|---|
| `attaques/` | texte exact des gabarits des quatre familles, points d'insertion, variantes — un YAML par famille, même format que `config/demo/attaques/`, `statut: GELE` | manuscrit |
| `taches/` | liste figée des tâches, avec la partition action-open / action-specifiee | manuscrit |
| `defenses/` | les six conditions, configuration exacte et version du code (dont Progent) | manuscrit |
| `juge/` | identifiant de version du modèle juge, prompt au caractère près, température, graine | manuscrit |

L'empreinte SHA-256 de ces dossiers, du plan et de l'archive WARC est écrite dans
chaque enregistrement (`empreinte_gel`). Tout changement après le gel la modifie :
il doit être consigné dans 07-TWEB-R2A/kit/DEVIATIONS.md.
