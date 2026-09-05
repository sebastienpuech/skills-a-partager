# mode-plan — notes, portabilité, limitations & historique

> Contenu de référence extrait de `SKILL.md` (progressive disclosure, v4.1). Jamais nécessaire pendant un run — consulter à la demande.

## Articulation mode-plan ↔ skill-auto-improver

`mode-plan` (ce skill) **conçoit** un skill incluant sa mémoire.
`skill-auto-improver` **exécute** la boucle de correction la nuit.

Pipeline complet :
1. mode-plan produit le plan + sessions CC qui codent la mémoire
2. Claude Code implémente le skill
3. Le skill tourne en prod et log dans `memory/`
4. skill-auto-improver lit `memory/issues.md` + ses test cases, propose des patches, commit/revert selon score
5. `proposed_fixes.md` sert d'audit trail

---

## Portabilité d'agents custom (Claude Code ↔ Cowork)

Format `.claude/agents/*.md` (Claude Code) ≈ format `references/adversarial/*.md` (skill) : frontmatter YAML identique, body = system prompt.

L'invocation diffère :
- **Claude Code** : `Task` tool accepte `subagent_type = <nom>`, lecture auto du `.md`.
- **Cowork** : `Task` tool n'accepte que les `subagent_type` standard. Pour invoquer un agent custom, **lire son .md** (Read) et passer le contenu comme prompt au `subagent_type: general-purpose`.

C'est ce que fait mode-plan avec les 6 agents de `references/adversarial/` — pattern portable par design.

---

## Limitations connues v3.2

- Types `skill` et `doc structuré` : templates app utilisés en dégradé.
- Refinement Loop max 3 rounds : Phase 3 peut coûter jusqu'à 5×3 = 15 spawns LLM (~50-100k tokens) sur un projet difficile. Reste raisonnable mais à monitorer.
- L'Observateur est optionnel et lui-même non auto-vérifié (pas de "méta-méta-cognitif"). Si l'Observateur a un biais, on ne le détectera qu'à l'usage.
- Pas de 3e itération automatique au-delà de 2 retours en Phase 2 (le Refinement Loop itère SUR le plan patché, pas SUR un re-draft from scratch).
- Pas de fallback si Task tool indisponible (skill suppose Cowork).
- `check_regression.py` utilise une heuristique keyword + négation — peut produire des faux positifs. À traiter comme alerte, pas comme blocage.
- Pattern injection (Phase 2.2) nécessite un fichier généré manuellement par pattern-extractor — pas encore d'orchestration automatique mode-plan → pattern-extractor → mode-plan.
- Les evals ne testent QUE les scripts Python (déterministes). **En v4.0 c'est corrigé** : `self_eval_debate.py` teste les agents LLM (critics, Défenseur, Juge, Observateur) via le self-golden-set rejouable.

### Plan de consolidation v4.0 (anti-bloat)

Si le SKILL.md dépasse 600 lignes OU si le fichier porte ≥ 4 patches en append, faire une réécriture vN.0 manuelle qui intègre les patches dans le body, reset le compteur, préserve l'historique via Git. mode-plan ne s'auto-consolide jamais. *(v4.1 : extraction de ce bloc + historique vers ce fichier pour rester sous 500 lignes — progressive disclosure.)*

---

## Historique de versions

- **v1.0** — Version initiale (4 fichiers, critic composite, handoff CC)
- **v1.2** — Gotchas, self-diagnosis, timeout/fallback critic, portabilité
- **v1.3** — Plan de consolidation anti-bloat, MCP fully qualified names
- **v1.4** — Mémoire du skill + articulation skill-auto-improver
- **v1.5** — AskUserQuestion développée, récap & validation, fast-track
- **v2.0** — Consolidation des patches v1.X dans le body principal
- **v3.0** — **Debate Room** (3 critics ∥ + Défenseur + Juge) remplace le critic composite. **Pattern injection** depuis plans réussis. **Self-diagnosis Python** (8 circuit-breakers). **Anti-régression** entre versions de patches.
- **v3.1** — Champ **Reset contexte** obligatoire par session (`nouvelle fenêtre` / `/clear` / `continuer`). Tableau de décision dans `references/handoff-cc.md`. Check #C9 dans `self_diagnosis.py`.
- **v3.2** — **Pattern 6 (Combo Debate Room + Refinement Loop)** : Phase 3 boucle max 3 rounds avec `check_convergence.py`. **Agent Observateur méta-cognitif** (Phase 3.6) qui détecte 8 biais structurels. **evals/** avec 9 golden cases + `run_evals.py` : 100% reproductible, 0 LLM, CI-ready.
- **v3.3** — **Harnais-Aware**. 4e critic `harnais` (Red Team H1–H8) dans la Debate Room ; sections harnais dans les 3 templates ; doctrine `references/harnais.md` ; gate `self_diagnosis.py --harness=on` (check C10) ; repondération `align_critiques.py` à 4 angles **rétro-compatible** (evals v3.2 inchangées, validées vertes : 11/11). Fondé sur l'état de l'art harnais 2025-2026.
- **v3.4** — **Harnais durci** (état de l'art Q4 2025–Q2 2026). Doctrine `references/harnais.md` + `critic-harnais` enrichis : **anti-gaming** (revers du RLVR, fondu dans H2/CRITIQUE) ; **split capability/regression** + grade-the-output (`spec` §10bis) ; **token-efficience des outils** (chargement différé / exécution par code, H7) ; **règle du writer unique** (écritures single-threaded, H8) ; **error-analysis** (lire les traces, H5). 5 sources ajoutées. **Aucun changement de scripts ni de la grille H1–H8** — evals inchangées (11/11).
- **v3.5** — **Boucle d'auto-amélioration du livrable**. Tout plan de type skill doit prévoir la boucle : signal rejouable + mémoire (`interactions`/`issues`/`proposed_fixes`) + moteur `skill-auto-improver` (commit si score↑/revert sinon) + déclencheur planifié + garde-fou anti-gaming. Câblage : doctrine `harnais.md` (couche + H4b) + `spec` §11 + check `critic-harnais` H4b + gate `self_diagnosis.py --autoimprove=on` (check C11, **skill-only, rétro-compatible**) + session CC §4.4 étendue + 2 golden cases (13 au total). mode-plan ne s'auto-réécrit pas en run.
- **v3.6** — **Handoff fichier-resident**. Le plan ne se colle plus : mode-plan génère un `CLAUDE.md` (Phase 4.3bis) pour la racine du repo cible (règle de fer + pointeurs vers les 4 fichiers + discipline harnais), lu automatiquement par Claude Code → contexte persistant qui survit aux resets. Doctrine `handoff-cc.md` mise à jour, gate `self_diagnosis.py --handoff=on` (check C12, accepte `CLAUDE.md` ou `AGENTS.md`, **off par défaut → rétro-compatible**), 2 golden cases (15 au total). Le format self-contained reste en fallback.
- **v4.0** — **Self-golden-set** : mode-plan se mesure enfin lui-même. `self_eval_debate.py` teste les AGENTS LLM (table de dispatch fermée, replay déterministe, provenance sha256 → `STALE_FIXTURE`) ; `verify_citations.py` (ancrage non-gamable) ; `_meta_eval.py` (grader-of-graders, 3 polarités) ; passe H8 d'ablation datée (`h8_ablation.py`) ; hold-out anti-gaming ; gate `--selfeval=on` (C13) ; boucle d'auto-amélioration (`auto_improve.py`, gate capability/regression/holdout, déclencheur manuel) ; doctrine avril 2026 (harnais 3-agents + context-resets) ; `journal.md`. Champ `hook` (H1–H8) sur les critics. Corpus S1–S8 + meta + hold-out. Construit en 5 sessions (dogfood).
- **v4.1** — **H9 + C14** (limites LLM du domaine, opt-in `--llmlimits`, `diagnostic-plafonds` front-door, template §12bis). **score_convergence dé-borné** (`score_convergence_raw` → fin des faux PLATEAU par saturation). **Couverture H8** : cas S9 (architecte+pragmatiste) + S10 (observateur, clé `contient_biais`) → 7/7 agents `garder`. Progressive disclosure : extraction de ce fichier pour tenir SKILL.md < 500 lignes.
- **v4.4** — **Le plan qui finit** (leçon du un chantier pro, 30/08/2026 : 7 plans successifs à jalons locaux binaires tous atteints, aucun état final global — chaque chantier clos rouvert sous 24-48 h ; modèle : un plan d'atterrissage d'un dépôt pro). Trois obligations pour TOUT plan (étape 2.4ter) : **condition d'arrêt globale** (§10ter, recette d'acceptation gelée sur cas réels, extérieure au code, verte = plan clos, survit aux découvertes) ; **décisions figées** (§9 re-templé : zéro « À trancher » résiduel, une seule gate G1 avant la Session 1, zéro question en vol) ; **régime des surprises** (section GATES de `sessions_claude_code.md` + génération de `TROUVAILLES.md` en 4.3ter : une découverte = une ligne, jamais une réouverture ni un plan concurrent). Gate `self_diagnosis.py --arret=on` (check C16, **off par défaut → evals inchangées, 23/23**). Corrigé au passage : artefact `\n` littéral dans la commande de l'étape 4.5.
- **v4.5** (2026-09-05) — **La recette a un lecteur et des formats, le plan lit ses leçons** (incident source : repo `un dépôt pro`, chantier `un chantier pro`, 30/08 → 05/09, 7 jours pour 3 estimés ; fiches `lecons/2026-09-05-*.md`, rangées dans le socle `claude-config/lecons/`).
  (1) Étape 2.4ter : la recette NOMME son lecteur (propriétaire ou relecteur hors session productrice — un vert du producteur est une précondition, pas une clôture) et sa cadence (après chaque lot), et LISTE les formats d'entrée, un cas gelé par format. Mesuré : recette déclarée verte le 02/09 par la session productrice (30 constats lus à la main), démentie le 03/09 par le propriétaire (10 défauts, 15 remarques) ; 66 tests verts sur un seul format, 1 question sur 134 lue sur la première base d'un autre format.
  (2) Nouvelle étape 2.0 : l'index des leçons (`lecons_index.py`, repli : `titre:` des `lecons/*.md`) entre dans la Debate Room ; une leçon applicable ignorée = critique CRITIQUE ; titres seulement.
  (3) Piège « répondre à une remarque du propriétaire par une architecture » (03/09 : quatre passes sous-agent, jours 5 à 7 sur 7, jamais tournées de bout en bout au 04/09) — une remarque devient un cas de recette.
  Gate C16 étendue dans `self_diagnosis.py` (lecteur + formats dans §10ter) ; off par défaut → evals inchangées, 23/23.
- **v4.3** — **Handoff exécutif délégué**. Le `CLAUDE.md` du repo cible et l'en-tête de `sessions_claude_code.md` désignent `superpowers:subagent-driven-development` (exécution tâche par tâche, contexte frais) + `superpowers:verification-before-completion` (gate anti-« done » prématuré) pour la descente, avec fallback explicite si le plugin est absent. **Par délégation, jamais par copie** : aucun texte d'Anthropic n'entre dans le repo, la mise à jour du plugin profite au plan. Aucune gate ajoutée (préférence d'exécution, pas prérequis de livraison) ; réversible en supprimant un bloc du template `handoff-cc.md`. Corrigé au passage : le `description` du frontmatter annonçait « 3 critics » depuis l'ajout de critic-harnais en v3.3.

---

## Référence d'exemple vivant

Le projet Coach du mainteneur est l'exemple canonique de ce que mode-plan produit. Voir `examples/coach-project/README.md` pour le contexte.
