## §10bis. Harnais & signal de succès

Le skill réussit si, pour un article donné, il produit **exactement 3 phrases** couvrant l'idée principale sans hallucination ni détail secondaire noyant l'essentiel. On mesure ça sur un **golden set de 10 à 15 articles** (formats variés : actu courte, enquête longue, tribune, papier technique) chacun accompagné d'un résumé de référence rédigé à la main.

**Signaux automatiques (à chaque run sur le golden set) :**
- **Contrainte de forme** : le résumé compte strictement 3 phrases (assert programmatique). Tout écart = échec net.
- **Fidélité factuelle** : aucune affirmation absente de l'article source (vérif LLM-juge « chaque phrase est-elle étayée par le texte ? », zéro toléré).
- **Couverture** : l'idée principale de la référence est présente (LLM-juge de similarité sémantique, seuil ≥ 0,7).

**Signal humain (échantillon) :** le mainteneur relit 3 résumés tirés au sort et tranche « je le lirais à la place de l'article ? » — objectif ≥ 8/10 acceptés sans retouche. Toute régression sur ces trois métriques bloque le déploiement.
