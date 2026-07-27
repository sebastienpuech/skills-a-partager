# spec — agrégateur de rapports (app)
## Vision
Un outil qui fusionne les rapports de N analyseurs en un seul fichier.
## Signal de succès
- Golden set: 3 jeux de rapports -> fichier fusionné attendu asserté (diff binaire).
## Fonctions
1. Lancer N analyseurs. 2. Chaque analyseur écrit sa part. 3. Produire le rapport.
