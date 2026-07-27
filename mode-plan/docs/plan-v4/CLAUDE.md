# CLAUDE.md — mode-plan v4.0

> Spec persistante de l'agent, lue automatiquement par Claude Code à chaque session.
> Générée par mode-plan (dogfooding). Les 4 fichiers du plan sont la source de vérité — ne pas les recopier, les LIRE.

## Règle de fer (immuable)
- mode-plan ne se réécrit JAMAIS en cours de run ; append-only partout.
- Le self-golden-set est le prérequis : aucune techno frontière+ (best-of-N, ensemble, L3) codée avant que la mesure existe ET prouve un gain de +0.03.
- Rétro-compat dure : les 15 evals v3.x restent vertes ; tout nouveau gate est opt-in par flag.
- Une seule fonction de normalisation (`scripts/_normalize.py`) — interdit de la redéfinir.
- Ce qui est mesuré peut être poussé ; ce qui n'est pas mesuré ne se code pas.

## Plan — à lire avant toute session
- `spec_produit.md` — vision, périmètre V1/V2 (§4), scénarios golden (§5), self-golden-set (§10bis), boucle d'auto-amélioration (§11), + Patches v1.1.
- `archi.md` — composants V1 (§2), L3 (§3), couche harnais §4bis, + Patches v1.1.
- `data_model.md` — seed de référence (§1), contrats d'exécution, gate d'adoption (§5), + Patches v1.1.
- `sessions_claude_code.md` — 5 sessions V1 + statut [DONE] + backlog V2.
- `journal.md` — état actuel glissant + log daté (prévu vs réalisé).

## Discipline harnais (non négociable)
- Session 1 construit le self-golden-set AVANT tout le reste.
- Fin de CHAQUE session : re-run `self_eval_debate.py --replay` + les 15 evals v3.x. Une feature n'est « done » que si elle passe de bout en bout.
- git : workspace clean avant tout changement ; commit par session/sprint ; revert si régression.
- Fin de session : mettre à jour `sessions_claude_code.md` ([DONE] + Décisions + Divergences) ET `journal.md`.

## Reset contexte
Dans le doute : nouvelle fenêtre. (cf. `sessions_claude_code.md`, table Reset contexte.)

## Finding méta (à garder en tête)
Le dogfooding a révélé un défaut de mode-plan lui-même : `score_convergence` est borné à 0, donc round 1 (−9 brut) et round 2 (−6,1 brut) affichent tous deux 0,0 → PLATEAU déclenché par saturation, pas par vraie convergence. Candidat v4.1 : dé-borner / normaliser le score pour que le Refinement Loop voie l'amélioration dans le bas de l'échelle.
