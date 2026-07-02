# archi — log-collector
## Composants
- collector.py, parser.py, indexer.py, dashboard.py
## Flux
- collector.py appelle indexer.py qui appelle parser.py qui appelle collector.py (dépendance circulaire). L'état global vit dans un singleton mutable partagé, écrit par tous les composants sans coordination.
## Garde-fous
- timeout 10s par fichier.
