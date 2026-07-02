# archi — log-merger
## Flux d'écriture
- Les N workers écrivent EN PARALLÈLE dans le même `merged.log` (chacun append sa part).
## Garde-fous
- timeout 20s.
