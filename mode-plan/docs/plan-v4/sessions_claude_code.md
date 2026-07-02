# Sessions Claude Code — mode-plan v4.0

> Plan d'exécution session par session. V1 = l'instrument de mesure (L1 core + L2 durcissement). V2 (best-of-N, ensembles, L3) = backlog après que le self-golden-set mesure.
> À garder ouvert en parallèle du terminal CC. Mettre à jour à la fin de chaque session.

---

## 🔒 RÈGLE DE FER — à coller au début de CHAQUE prompt CC

```
IMPORTANT — règle de fer du projet mode-plan v4.0 :
- mode-plan ne se réécrit JAMAIS en cours de run ; append-only sur tous les fichiers.
- Le self-golden-set est le prérequis : aucune techno frontière+ (best-of-N, ensemble, L3) codée avant que la mesure existe et prouve un gain.
- Rétro-compat dure : les 15 evals v3.x doivent rester vertes ; tout nouveau gate est opt-in par flag.
- Une seule fonction de normalisation (`scripts/_normalize.py`) ; interdit de la redéfinir ailleurs.
- Si tu vois du code qui viole ça, signale-le et corrige-le.
```

## 🛡️ PROTOCOLE ANTI-RÉGRESSION (toute session)

`git status` clean avant tout changement. Commit par session (ou par sprint interne). `git tag session-N`. Si régression : `git reset --hard HEAD~1`, fix, retry. Rollback fichier : `git checkout HEAD~1 -- path`.

## 🧪 HARNAIS D'ABORD

Session 1 construit le self-golden-set (le signal de succès) AVANT tout le reste. Fin de CHAQUE session : re-run `self_eval_debate.py --replay` + les 15 evals v3.x. Une feature n'est « done » que si elle passe de bout en bout.

---

### Session 1 — Le self-golden-set (le cœur, à faire en premier)

**Statut** : [DONE] 2026-07-01 (construit dans `meta/skills/mode-plan/`, additif à v3.6)
**Objectif** : construire l'instrument qui mesure enfin les agents LLM de mode-plan.
**Prérequis** : repo v3.6 en place (cf. spec §0bis).
**Reset contexte** : `nouvelle fenêtre`

**Prompt** :
```
[RÈGLE DE FER ci-dessus]

On construit le self-golden-set de mode-plan v4.0. Lis spec_produit.md §5+§10bis, data_model.md §1+§2+§6, archi.md §2.1+§2.3+§2.4 (+ les patches v1.1 en bas de chaque fichier).

Tâche :
1. `scripts/_normalize.py` : la fonction `norm()` (spec exacte data_model §3 patch + archi §2.1).
2. `evals/selfeval/` : créer les 8 cas S1–S8. Au MINIMUM le cas S1_no_golden_set complet (3 .md réels + expected.json) exactement comme data_model §1. Les autres cas : 3 .md + expected.json + `recorded/<agent>.json` (sorties d'agents enregistrées) pour le mode replay.
3. `scripts/self_eval_debate.py` avec le contrat archi §2.3 : mode `--replay` (déterministe, lit recorded/) ET `--live`. Dispatch table fermée expected_verdicts→prédicat (patch SIM-002/003). recorded/ + expected.json en lecture seule (patch HARN-001).
4. `scripts/_meta_eval.py` : grader-of-graders, 3 polarités (patch HARN-002).

Plan d'abord, je valide avant que tu agisses.
```

**Vérifications** : `python3 scripts/self_eval_debate.py --replay` sort un `selfeval_report.json` valide ; `_meta_eval.py` passe ; S1 doit fire, S2 (Garde-fous) ne doit pas fire.
**Commit** : `feat: self-golden-set + self_eval_debate (replay) + meta-eval`
**MAJ plan** : `[DONE]` + Décisions + Divergences dans ce fichier + `journal.md`.

**Décisions (réalisé)** :
- Livrables construits **in-place dans `meta/skills/mode-plan/`** (le skill v3.6), purement additifs — aucune réécriture v3.6. Le §0bis rend les chemins relatifs à ce repo.
- `_normalize.py` : ordre exact archi §2.1 (lower → NFKD sans diacritiques → apostrophes/guillemets typo → collapse ws → strip ponctuation terminale). Source unique.
- `self_eval_debate.py` : frontière nette `collect_agent_outputs()` (seule à connaître live/replay + provenance sha256 → `STALE_FIXTURE`) / `grade()` pure avec **table de dispatch fermée** (`contient_gravite`+`sur_hook`, `au_moins_une`, `aucun_trouve_sur`, `should_not_fire`). Toute clé hors table = fail explicite. Budget `--live` (max_spawns=50 / 15 min / échantillon 3).
- `recorded/<agent>.json` = wrapper `{_provenance{agent_file,agent_sha256,recorded_at}, output}` ; `output` = JSON brut d'agent (même parseur live/replay, patch SIM-001).
- Champ `hook` (H1…H8|null) ajouté au schéma des **4 critics** (SIM-003) — additif, n'affecte pas les 15 evals.
- 8 seeds S1–S8 : **S1/S2/S7 gradés en replay** (verts) ; **S3/S4/S5/S6/S8** = `graded_by` (verify_citations / fs_refus / l3_gate / adoption_gate / holdout) → skip propre par self_eval_debate (câblés en Sessions 2/4/V2).
- `_meta_eval.py` : boîte noire (ARCH-R2-004), pilote le **vrai** `self_eval_debate --replay` ; 3 polarités (no_fire→fail, fire_correct→pass, faux_positif→fail) → **green**.

**Divergences** :
- `python3` est cassé sur la machine (stub WindowsApps) → scripts invoqués avec `python` ; tout appel inter-script utilise `sys.executable` (jamais `python3`). Le durcissement de `run_evals.py` (hardcode `python3` ligne 138) reste pour la **Session 4**. Baseline & re-run des 15 evals faits via un shim `python3.exe` de session.
- S2 : la table fermée ne couvre que `aucun_trouve_sur` (négatif) ; l'assertion positive **Défenseur TROUVÉ + ancré** dépend de `verify_citations` → câblée en **Session 2** (documentée en `deferred_assertions` dans `S2/expected.json`, `recorded/defenseur.json` déjà fourni).
- `evals/selfeval/selfeval_report.json` = artefact runtime → gitignore.

**Vérifs exécutées (evidence)** : `self_eval_debate --replay` → 3/3 pass, 4 skipped, `selfeval_report.json` valide ; S1 fire, S2 (Garde-fous) ne fire pas, S7 fire ; STALE_FIXTURE testé (hash faux → fail + exit 1) ; `_meta_eval` → 3/3 green (3 polarités) ; `run_evals` → **15/15**.

---

### Session 2 — verify_citations + anti-staleness replay

**Statut** : [DONE] 2026-07-01
**Objectif** : tuer la surface d'hallucination des citations + verrouiller le replay.
**Prérequis** : Session 1.
**Reset contexte** : `/clear`

**Prompt** :
```
[RÈGLE DE FER]

Lis archi.md §2.2 + data_model §3 + les patches HARN-001/ARCH-R2-002.
Tâche :
1. `scripts/verify_citations.py` : normalise via `_normalize.norm`, cherche chaque passage_cite/passage_verifie dans la source, sort `citations_report.json`, downgrade les non-ancrées.
2. Anti-staleness replay : stocker un hash du .md d'agent dans recorded/ ; la CI échoue si le .md a changé sans re-enregistrement.
3. Câbler verify_citations en post-étape de la Debate Room (après le Juge).

Plan d'abord.
```

**Vérifications** : une citation inventée est flaggée `non_ancre` ; modifier un `.md` d'agent fait échouer le replay tant qu'on n'a pas re-enregistré.
**Commit** : `feat: verify_citations + replay anti-staleness`

**Décisions (réalisé)** :
- `scripts/verify_citations.py` : cœur PUR `is_anchored(passage, source_texts)` (norm + substring, 0 I/O) + `build_report()` → `citations_report.json` (data_model §3). Extraction par forme de sortie (critics `passage_cite` / défenseur `passage_qui_repond` / juge `passage_verifie`) ; absences déclarées (section ABSENTE, « aucune section… ») non comptées. Actions de downgrade portées dans le rapport.
- **Item 2 (anti-staleness) déjà livré en Session 1** (`_provenance.agent_sha256` + `STALE_FIXTURE`, ARCH-R2-002). Session 2 le **renforce** d'un `.gitattributes eol=lf` (sha stables cross-platform) et le **démontre end-to-end**.
- **Câblage** : (a) `verify_citations` post-Juge documenté en SKILL.md **Étape 3.4bis** (actions de downgrade consommées avant l'Étape 4.1) ; (b) intégré au self-golden-set — S3 désormais **gradé** par verify_citations (plus skippé) ; (c) assertion positive **S2 débloquée** : nouvelle clé `trouve_sur_ancre` dans la table fermée (`grade()` reste pure, sources passées par `run_case`), documentée en `data_model` Patches v1.2.

**Divergences** :
- Table de dispatch fermée **étendue** (5e clé `trouve_sur_ancre`) — décision d'implémentation assumée et documentée (data_model v1.2), nécessaire au scénario S2 du spec.
- `citations_report.json` = artefact runtime → gitignore.

**Vérifs exécutées (evidence)** : S3 citation inventée → `non_ancre` (taux 0.0) ; S2 citation Défenseur → ancrée (taux 1.0) ; `self_eval_debate --replay` → **4/4 pass** (S1/S2/S3/S7), 4 skipped ; anti-staleness : modif de `critic-harnais.md` → 3× STALE_FIXTURE + exit 1, restore → 4/4 ; `_meta_eval` 3/3 green ; `run_evals` **15/15**.

---

### Session 3 — Passe H8 sur le fan-out hérité (solde la dette v3.6)

**Statut** : [DONE] 2026-07-01
**Objectif** : mesurer enfin si chaque agent hérité mérite sa place.
**Prérequis** : Sessions 1-2.
**Reset contexte** : `nouvelle fenêtre`

**Prompt** :
```
[RÈGLE DE FER]

Lis archi.md §2.5 + data_model §5 (D2) + §7.
Tâche : pour chaque agent hérité (4 critics, Défenseur, Juge, Observateur), rejoue le self-golden-set SANS lui (ablation) et calcule le delta orienté (data_model §5bis patch). Écris `_mode-plan-meta/h8_ablation_<date>.md` (tableau agent | avec | sans | delta | garder/simplifier). NE supprime aucun agent — produis seulement la recommandation datée.

Plan d'abord.
```

**Vérifications** : le rapport existe, daté, avec une décision par agent.
**Commit** : `chore: passe H8 ablation datée sur le fan-out hérité`

**Décisions (réalisé)** :
- `scripts/_constants.py` : `SEUIL_MIN = 0.03` **source unique** (SIM-004) — consommé par la décision D2.
- **Ablation** = vider la sortie de l'agent (`{}`) plutôt que la retirer : les should-fire qui en dépendent échouent, les should-not-fire passent (vacuité) → sémantique correcte. Ajout d'un flag `--ablate <agent>` à `self_eval_debate` (param optionnel threadé, n'affecte pas le run normal).
- `scripts/h8_ablation.py` : baseline (fan-out complet) + score ablaté par agent ; **gain_oriente = baseline − score_sans** (convention D2, §5bis) ; garder SSI `gain_oriente >= SEUIL_MIN`. Écrit `_mode-plan-meta/h8_ablation_<date>.md` (+ `.json` machine-lisible). **Ne supprime aucun agent.**
- 3e décision ajoutée à côté de garder/simplifier : **`non_exerce`** (gain_oriente == 0) — l'agent n'est pas testé par le corpus actuel ; c'est un trou de couverture, PAS une preuve d'inutilité.

**Finding H8 (2026-07-01)** : sur le corpus actuel (S1/S2/S3/S7 gradés), baseline=1.0.
- **garder** : critic-harnais (gain 0.5, 4 cas), critic-simulateur / defenseur / juge (gain 0.25 chacun).
- **non_exerce** : critic-architecte, critic-pragmatiste, observateur (gain 0.0) → le corpus ne les exerce pas encore. **Prochain levier** : écrire des cas golden qui exercent ces 3 agents avant toute décision de simplification.

**Vérifs exécutées** : `h8_ablation.py` → rapport daté `_mode-plan-meta/h8_ablation_2026-07-01.md` avec 1 décision/agent (7 agents) ; `self_eval_debate --replay` reste **4/4** (run normal intact) ; `_meta_eval` 3/3 green ; `run_evals` **15/15**.

---

### Session 4 — Durcissement scripts + hold-out + gate C13

**Statut** : [DONE] 2026-07-01
**Objectif** : solder les fragilités et opérationnaliser l'anti-gaming.
**Prérequis** : Session 1.
**Reset contexte** : `/clear`

**Prompt** :
```
[RÈGLE DE FER]

Lis archi.md §2.6 + §5 + les patches HARN-003 (hold-out) + ARCH-R2-001 (gate signe).
Tâche :
1. Durcir : `align_critiques.py` (dedup via norm), `check_convergence.py` (try/except → décision ERROR), `check_regression.py` (détection langue + cap alertes).
2. `evals/selfeval/_holdout/` : cas réels tenus hors optimisation, lecture seule pour le moteur ; le moteur rejoue le hold-out après chaque patch, regression_holdout<100% → revert auto.
3. `self_diagnosis.py --selfeval=on` → C13 (corpus existe, replay tourne, meta-eval passe).

Plan d'abord.
```

**Vérifications** : `check_convergence` sur un JSON malformé retourne ERROR (pas de crash) ; `self_diagnosis --selfeval=on` passe ; les 15 evals v3.x vertes.
**Commit** : `feat: script hardening + hold-out + C13`

**Décisions (réalisé)** :
- `align_critiques.py` : `detect_duplicates` compare `(norm(fichier), norm(section))` — sur-ensemble de l'égalité exacte, rattrape les quasi-doublons.
- `check_convergence.py` : parse d'un round dans un try/except élargi → **décision `ERROR`** en stdout + exit 0 (mode safe, plus de crash exit 2).
- `check_regression.py` : `detect_language` (FR/EN) + `STOPWORDS_EN` + marqueurs de négation EN ; **cap `--max-alerts` (défaut 20)** trié par gravité (CONTRADICTION avant REPEAT) avec `alerts_truncated` explicite (pas de troncature muette, H5).
- `evals/selfeval/_holdout/` : 2 cas réels (HO1 trou H2, HO2 should-not-fire) + `README.md` fixant la règle **lecture-seule + rejoue après patch + revert si <100 %** (HARN-003/ARCH-006). Séparés par le préfixe `_` → jamais dans la suite capability normale.
- `self_diagnosis.py --selfeval=on` → **C13** : porte sur le SKILL lui-même (SKILL_ROOT), lance `self_eval_debate --replay` + `_meta_eval` via `sys.executable`. Opt-in → 9 checks par défaut inchangés.

**Divergences** :
- Aucune régression : 15/15 evals v3.x restent vertes malgré la modif de 4 scripts v3.6 (durcissements strictement additifs en comportement).
- Le **revert auto** sur hold-out est la *règle* (README) ; son câblage effectif dans le moteur est en **Session 5** (skill-auto-improver).

**Vérifs exécutées** : hold-out `--replay` **2/2** ; `check_convergence` JSON malformé → `decision=ERROR`, exit 0 ; `self_diagnosis --selfeval=on` sur le plan v4 → **status PASS, 13 checks, 0 échec** (C13 inclus) ; `run_evals` **15/15**.

---

### Session 5 — Doctrine avril 2026 + progressive disclosure + boucle d'auto-amélioration

**Statut** : [DONE] 2026-07-01 — **clôture V1 (5/5)**
**Objectif** : mettre la doctrine à la frontière + brancher la boucle (déclencheur manuel V1).
**Prérequis** : Sessions 1-4.
**Reset contexte** : `nouvelle fenêtre`

**Prompt** :
```
[RÈGLE DE FER]

Lis spec §11 + archi §4bis.
Tâche :
1. `references/harnais.md` : ajouter le harnais 3-agents Planner/Generator/Evaluator + context-resets-over-compaction (avril 2026), en append (ne pas réécrire).
2. Générer `journal.md` en Phase 4 du workflow + pointeur dans CLAUDE.md.
3. Boucle d'auto-amélioration V1 : `_mode-plan-meta/` (interactions.jsonl, issues.md, proposed_fixes.md) + hook skill-auto-improver (lit issues+golden set, commit si capability↑ ET regression==100% ET holdout==100% / revert). Déclencheur = MANUEL en V1 (documenter la tâche planifiée hebdo comme forme-cible).
4. Check progressive disclosure : SKILL.md ≤ 500 lignes (sinon signaler).

Plan d'abord.
```

**Vérifications** : une passe manuelle de skill-auto-improver à sec ne commit rien si le score ne monte pas ; `journal.md` généré.
**Commit** : `feat: doctrine 2026 + auto-improve loop (manual trigger) + journal`

**Décisions (réalisé)** :
- `references/harnais.md` : append d'une section « Ajout avril 2026 (v4.0) » — harnais 3-agents **Planner/Generator/Evaluator** + **context-resets over compaction** + 3 sources. Aucune réécriture au-dessus.
- `_mode-plan-meta/` complété : `issues.md` (seedé avec 2 findings réels : score_convergence borné → v4.1, et le trou de couverture H8), `proposed_fixes.md` (audit trail), `interactions.jsonl` (métadonnées only, 1 ligne dogfood).
- `scripts/auto_improve.py` : mesure les **3 métriques du gate** (capability / regression / holdout) ; **gate** = `capability↑ ET regression==1.0 ET holdout==1.0` ; `--dry-run` (défaut, seul mode V1) **ne touche jamais git** ; audit dans `proposed_fixes.md`. Déclencheur MANUEL (tâche hebdo = forme-cible documentée).
- **Check progressive disclosure** intégré à `auto_improve.py` : SKILL.md ≤ 500 lignes sinon signale.
- `journal.md` **câblé dans le workflow** : SKILL.md **Étape 4.3ter** (génération selon data_model §4) + pointeur `journal.md` ajouté au template CLAUDE.md (`references/handoff-cc.md`).

**Divergences / findings** :
- **SKILL.md = 542 lignes > 500** → le check progressive disclosure **signale** (attendu). < 600 (seuil de consolidation dure de la règle anti-bloat) → non bloquant. Candidat à une consolidation vN.0 (déplacer du contenu vers `references/`) — noté dans `issues.md` (à traiter hors V1).
- Le moteur LLM (`skill-auto-improver`) qui *génère* le patch reste externe ; `auto_improve.py` fournit la mesure + le gate + l'audit (frontière Planner/Evaluator).

**Vérifs exécutées** : `auto_improve --dry-run` → **NO_COMMIT** (capability ne monte pas) + signale SKILL.md 542>500 ; `journal.md` présent et à jour ; `self_eval_debate --replay` **4/4** ; `_meta_eval` **3/3** ; `self_diagnosis --selfeval=on` **PASS 13/13** ; `run_evals` **15/15**.

---

## V2 — Backlog (NE PAS coder en V1)

Sessions futures, seulement APRÈS que le self-golden-set mesure : best-of-N réel (le gate à sec est en V1), ensemble de vérifieurs cheap, phase L3 (diagnostic-plafonds→labo-recherche→gate→application-solutions), déclencheur cron. Chacune gatée : n'entre que si elle fait +0.03 de score capability.

## Table Reset contexte

| Session | Reset | Pourquoi |
|---|---|---|
| 1 | nouvelle fenêtre | démarrage propre |
| 2 | /clear | courte, enchaîne S1 |
| 3 | nouvelle fenêtre | ablation = beaucoup de spawns |
| 4 | /clear | enchaîne, scripts |
| 5 | nouvelle fenêtre | doctrine + boucle, session lourde |
