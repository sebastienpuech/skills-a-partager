# archi — agrégateur de rapports
## Flux d'écriture
- Les N analyseurs écrivent EN PARALLÈLE dans le même fichier `report.json` (chacun append sa section).
## Garde-fous
- timeout 30s par analyseur.
