# Hold-out — cas tenus hors optimisation (HARN-003)

Ces cas ont **exactement le même schéma** que `evals/selfeval/` mais vivent dans un
dossier séparé (préfixé `_`, donc jamais découverts par la suite capability normale).

**Règle (anti-gaming)** :
- Le moteur d'auto-amélioration (`skill-auto-improver`, Session 5) **n'optimise JAMAIS
  contre ces cas** — il ne les voit pas pendant l'optimisation.
- Après chaque patch, il **rejoue le hold-out** : `self_eval_debate.py --replay --dir evals/selfeval/_holdout`.
- Si `regression_holdout < 100 %` → **revert automatique** du patch. On surveille la
  généralisation hors-distribution, pas seulement le score du golden set d'optimisation.
- `expected.json` + `recorded/` du hold-out sont **en lecture seule** pour le moteur
  (au même titre que le reste du golden set — ARCH-006).
