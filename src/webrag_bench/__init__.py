"""webrag-r2a-bench — banc de mesure retrieval -> action.

Mesure par étages emboîtés : exposition -> absorption -> effet -> action.
Aucun site tiers n'est contacté : toutes les pages viennent d'une archive WARC locale.
"""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
