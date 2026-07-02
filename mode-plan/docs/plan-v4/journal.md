# journal — mode-plan v4.0

## État actuel  (réécrit en tête à chaque MAJ)
- **Phase** : V1 close + v4.1 (3 findings clos) + **V2-1 (best-of-N) : ADOPTÉ**.
- **Sessions faites** : 5/5 (V1) + 4 patchs v4.1 + V2-1 best-of-N.
- **V2 — best-of-N : ADOPTÉ ET CÂBLÉ** (opt-in). Consolidé sur **8 cas gradués** (BN1-8), mesure LIVE (24 vrais agents rédacteurs au total) : baseline 0,45 → candidate 0,5625, **gain_oriente 0,1125 ≥ 0,03**. Le gain tient (0,10 sur 3 cas → 0,1125 sur 8). Câblé en **SKILL.md Étape 2.4bis** (`--bestofn=on`, N=2, writer-unique, ×2 sur la seule section §10bis, OFF défaut). `best_of_n.py --select` = le sélecteur. 2 cas à variance nulle (BN2, BN4) — best-of-N n'aide pas partout, honnête.
- **V2 item ② — ensemble de vérifieurs : NON câblé (décision d'efficience).** Correction : sous forfait **Max** (Agent SDK, tarif à plat), « vérifieurs cheap » n'a aucun sens (Opus/Haiku coûtent pareil) → re-mesuré **100% Opus**. 8 cas de vérification difficiles, LIVE : baseline **1 Opus 0,875** = candidate **3 Opus (vote) 0,875** → **gain 0,0**. Ensembler le même modèle fort n'apporte aucune justesse (le seul raté EV6 est systématique, pas du bruit ; le vote ne corrige que le bruit). Coût ×3 latence/tokens pour 0 gain → **décision d'efficience : non câblé** (garder le Juge unique). `ensemble_verifiers.py` livré + `--check` en CI. *(1er run Haiku −0,125 : hors-sol, superseded.)*
- **V2 item ③ — déclencheur cron : LIVRÉ (non enregistré).** Opérationnalise la boucle d'auto-amélioration en passe hebdo. `auto_improve.py --log` (métadonnées → `interactions.jsonl`) + wrapper `auto_improve_cron.ps1` + installeur `register_cron.ps1` (tâche utilisateur, dimanche 03:00, trigger temporel + StartWhenAvailable = survit à la veille) + doc `CRON.md`. Pas de gate (c'est un trigger, pas une capacité). NON enregistré sur la machine (changement système, à lancer par Sébastien). V1 : la passe mesure + log, ne commit rien (l'étape LLM de patch reste séparée).
- **V2 item ④ — phase L3 : gate statique LIVRÉ.** Chaîne diagnostic-plafonds→labo→gate→application (opt-in `--l3=on`, skill stratégique). Le cœur déterministe = `l3_gate.py` : une trouvaille du labo entre au draft SSI **ancrée** (`is_anchored(passage_source, sources)` = anti-hallucination) ET **exprimable** (cas_de_test_futur non vide) ; sinon backlog. Gate 2-temps (statique maintenant, dynamique après build du skill cible = reporté). Golden `evals/l3/` + cas eval → run_evals 22/22. Doctrine `references/l3.md`. La chaîne LLM (diagnostic/labo/application) = orchestration documentée, non scriptée.
- **Findings** : #1, #2, #3 tous clos. **V2 : ①câblé ②non-câblé ③cron ④L3-gate — les 4 items traités.**
- **Prochain pas** : enregistrer le cron (`register_cron.ps1`) ; étoffer le hold-out (2→N) ; câbler la génération LLM de patch (skill-auto-improver) dans le sandbox ; gate L3 dynamique quand un skill stratégique réel est construit.

---

## Log (append-only, daté)

### 2026-07-01 — Phase 1-2 (élicitation + draft)
- **Prévu** : spec 3 couches (L1/L2/L3), self-golden-set, verify_citations, harnais 3-agents.
- **Réalisé** : draft des 3 fichiers.
- **Divergence** : aucune à ce stade.

### 2026-07-01 — Phase 3 round 1 (Debate Room)
- **Prévu** : challenger le draft.
- **Réalisé** : 4 critics (arch 5, prag 5, sim 4, harnais 7) → 22 critiques → Défenseur (1 trouvé, 19 partiel, 2 pas trouvé) → Juge : 12 confirmées (3 CRITIQUE), score 0,0, **major_revision**.
- **Divergence** : le cœur (self_eval_debate.py, corpus, normalisation) était sous-spécifié — décision **redraft** (au lieu de patch).

### 2026-07-01 — Phase 2bis (redraft)
- **Réalisé** : réécriture des 3 fichiers intégrant les 12 critiques ; ajout des contrats d'exécution, du seed de référence réel, du split V1/V2, du grader-of-graders, de la passe H8.

### 2026-07-01 — Phase 3 round 2 (Debate Room)
- **Réalisé** : 4 critics (arch 7, prag 6, sim 5, harnais 5) → 18 critiques → Défenseur (0 trouvé, 5 partiel, 13 pas trouvé) → Juge : 12 confirmées (4 CRITIQUE surgicales), 3 rejetées (désaccords de priorité du Pragmatiste), score 0,0, major_revision.
- **Divergence notée** : les critiques round 2 sont « un cran plus profond » (schéma recorded/, dispatch table, champ hook, budget) — patchables, pas de 2e redraft.

### 2026-07-01 — Phase 4 (patch + livraison)
- **Réalisé** : 15 patches append-only v1.1 (12 confirmées + 3 partielles) sur les 3 fichiers ; convergence = PLATEAU ; génération sessions_claude_code.md + CLAUDE.md + ce journal.
- **Finding méta** : `score_convergence` borné à 0 masque l'amélioration round1→round2 (raw −9 → −6,1). PLATEAU par saturation. → candidat v4.1 (dé-borner le score). Ajouté à `_mode-plan-meta/issues.md` (à créer en Session 5).
- **Prochain pas** : Session 1.

### 2026-07-01 — Session 1 (self-golden-set) [DONE]
- **Prévu** : `_normalize.py`, `evals/selfeval/` (8 cas), `self_eval_debate.py` (replay+live), `_meta_eval.py` (grader-of-graders).
- **Réalisé** (dans `meta/skills/mode-plan/`, additif à v3.6) :
  - `scripts/_normalize.py` `norm()` (ordre exact archi §2.1, source unique).
  - `scripts/self_eval_debate.py` : frontière `collect_agent_outputs`/`grade` pure, table de dispatch **fermée**, provenance sha256 → `STALE_FIXTURE`, budget `--live`. Report `selfeval_report.json`.
  - 8 seeds `evals/selfeval/S1…S8` : S1 canonique complet (data_model §1) ; S2/S7 gradés replay ; S3/S4/S5/S6/S8 `graded_by` autre vérifieur (skip propre).
  - `scripts/_meta_eval.py` : grader-of-graders boîte noire, 3 polarités → green.
  - Champ `hook` (H1…H8|null) ajouté au schéma des 4 critics (SIM-003, additif).
- **Vérifs** : `self_eval_debate --replay` 3/3 pass + 4 skipped ; S1 fire / S2 Garde-fous non / S7 fire ; STALE_FIXTURE OK ; `_meta_eval` 3/3 green ; **15/15** evals v3.x.
- **Divergences** : (1) `python3` cassé (Windows Store) → `python` + `sys.executable` inter-scripts ; durcissement `run_evals.py` reporté en **Session 4**. (2) S2 assertion positive Défenseur-TROUVÉ-ancré reportée en **Session 2** (dépend de `verify_citations`) ; `deferred_assertions` documenté dans le seed. (3) `selfeval_report.json` gitignoré (artefact runtime).

### 2026-07-01 — Session 2 (verify_citations + anti-staleness) [DONE]
- **Prévu** : `verify_citations.py`, anti-staleness replay, câblage post-Juge.
- **Réalisé** :
  - `scripts/verify_citations.py` : cœur PUR `is_anchored()` + `build_report()` → `citations_report.json` (data_model §3), extraction par forme de sortie, absences déclarées ignorées, actions de downgrade.
  - Anti-staleness : **déjà livré en Session 1** (STALE_FIXTURE) ; renforcé par `.gitattributes eol=lf` + démontré end-to-end.
  - Câblage : SKILL.md **Étape 3.4bis** (verify_citations post-Juge) ; S3 gradé par verify_citations dans le self-golden-set ; **assertion positive S2 débloquée** via nouvelle clé fermée `trouve_sur_ancre` (`grade()` reste pure).
- **Vérifs** : S3 → non_ancre ; S2 → ancrée ; `self_eval_debate --replay` **4/4 pass** (S1/S2/S3/S7) ; anti-staleness modif→STALE_FIXTURE→restore→4/4 ; `_meta_eval` 3/3 green ; **15/15** evals v3.x.
- **Divergence** : table de dispatch fermée étendue (5e clé `trouve_sur_ancre`, positif ancré) — assumée et documentée (data_model Patches v1.2), requise par le scénario S2.

### 2026-07-01 — Session 3 (passe H8 ablation) [DONE]
- **Prévu** : ablater chaque agent hérité, calculer le delta orienté, écrire `_mode-plan-meta/h8_ablation_<date>.md`.
- **Réalisé** :
  - `scripts/_constants.py` (`SEUIL_MIN=0.03`, source unique SIM-004).
  - `--ablate <agent>` sur `self_eval_debate` (ablation = sortie vidée `{}`, sémantique correcte should-fire/should-not-fire).
  - `scripts/h8_ablation.py` : gain_oriente = baseline − score_sans (D2, §5bis) ; rapport daté `.md` + `.json` ; **aucune suppression**.
- **Finding** : baseline 1.0. garder → critic-harnais (0.5), simulateur/defenseur/juge (0.25) ; **non_exerce** (0.0) → architecte, pragmatiste, observateur. Le corpus sur-couvre critic-harnais et n'exerce pas 3 agents. Levier suivant : cas golden pour ces 3 agents.
- **Vérifs** : rapport daté 7 décisions ; `self_eval_debate --replay` 4/4 (run normal intact) ; `_meta_eval` 3/3 ; `run_evals` 15/15.
- **Divergence** : 3e verdict `non_exerce` ajouté (au-delà de garder/simplifier) pour distinguer « inutile » de « non testé » — évite une fausse recommandation de suppression.

### 2026-07-01 — Session 4 (durcissement + hold-out + C13) [DONE]
- **Prévu** : durcir 3 scripts, `_holdout/`, `self_diagnosis --selfeval=on` (C13).
- **Réalisé** :
  - `align_critiques` : dedup via `(norm(fichier), norm(section))`.
  - `check_convergence` : JSON malformé → décision `ERROR` (exit 0, plus de crash).
  - `check_regression` : détection FR/EN + stopwords EN + cap `--max-alerts` (20) trié par gravité, troncature explicite.
  - `evals/selfeval/_holdout/` : HO1 (trou H2), HO2 (should-not-fire) + README (lecture seule, rejoue+revert).
  - `self_diagnosis --selfeval=on` → C13 (SKILL_ROOT : replay + meta-eval via `sys.executable`), opt-in.
- **Vérifs** : hold-out 2/2 ; check_convergence malformé → ERROR/exit 0 ; `self_diagnosis --selfeval=on` sur plan v4 → **PASS 13/13** ; `run_evals` **15/15** (aucune régression sur les 4 scripts v3.6 modifiés).
- **Divergence** : câblage effectif du revert-auto sur hold-out reporté en Session 5 (la règle est posée dans le README).

### 2026-07-01 — Session 5 (doctrine 2026 + auto-improve + journal) [DONE] — clôture V1
- **Prévu** : doctrine avril 2026 (append harnais.md), journal.md en Phase 4, boucle d'auto-amélioration V1, check progressive disclosure.
- **Réalisé** :
  - `references/harnais.md` : append « Ajout avril 2026 » (harnais 3-agents Planner/Generator/Evaluator + context-resets over compaction + sources).
  - `_mode-plan-meta/` : `issues.md` (2 findings réels), `proposed_fixes.md` (audit), `interactions.jsonl` (1 ligne).
  - `scripts/auto_improve.py` : mesure capability/regression/holdout + gate `capability↑ ET regression==1.0 ET holdout==1.0` ; `--dry-run` ne touche jamais git ; check progressive disclosure intégré.
  - `journal.md` câblé : SKILL.md Étape 4.3ter + pointeur dans le template CLAUDE.md (handoff-cc.md).
- **Vérifs** : `auto_improve --dry-run` → NO_COMMIT (pas d'amélioration) + signale SKILL.md 542>500 ; `self_eval_debate` 4/4 ; `_meta_eval` 3/3 ; `self_diagnosis --selfeval=on` 13/13 ; `run_evals` 15/15.
- **Divergences** : SKILL.md 542>500 signalé (candidat consolidation vN.0, < 600 non bloquant) ; le générateur LLM du patch (`skill-auto-improver`) reste externe, `auto_improve.py` fournit mesure+gate+audit.

---

### 2026-07-01 — v4.1 (2 patchs post-V1)
- **Patch A — H9 + C14 (limites LLM du domaine)** : hook harnais H9 + gate C14 (`--llmlimits=on`), template §12bis, front-door `diagnostic-plafonds` (SKILL.md 2.0bis). 2 golden cases (17). critic-harnais.md re-stampé (8 fixtures). Tag `v4.1-h9-c14`.
- **Patch B — score_convergence dé-borné (finding #1 résolu)** : le Juge émet `score_convergence_raw` (non borné) ; `check_convergence.py` calcule le PLATEAU sur le brut → plus de faux PLATEAU par saturation (round −9→−6,1 = CONTINUE, plus PLATEAU). Fixture `convergence_plateau_vs_saturation` (18 evals). juge.md re-stampé (S1). Rétro-compat (fallback clampé si `raw` absent).
- **Patch C — couverture H8 des 3 agents (finding #2 résolu)** : cas S9 (défaut archi → architecte CRITIQUE + pragmatiste MAJEUR) + S10 (biais B3 → observateur, nouvelle clé fermée `contient_biais`). Passe H8 régénérée = **7/7 `garder`** (plus de `non_exerce`). Corpus self-golden-set : 6 cas gradés en replay (S1/S2/S3/S7/S9/S10).
- **Patch D — progressive disclosure (finding #3 résolu)** : extraction des 6 sections de queue de SKILL.md (551 → **492 lignes**) vers `references/notes-et-historique.md` (+ historique complété v4.0/v4.1). Check `auto_improve` progressive disclosure `ok=True`. Aucune régression.
- **Findings restants** : aucun. #1, #2, #3 clos.

### 2026-07-02 — V2-1 best-of-N testé, gain=0.10, adopté=oui
- **Prévu** : 1er item V2 — best-of-N, gaté sur +0.03 de capability (règle de fer).
- **Réalisé** :
  - `scripts/best_of_n.py` : rubrique déterministe 0-10 (6 critères §10bis, mots-clés via `_normalize`) + sélection best-of-N + gate D1. Flag `--bestofn=on` (OFF défaut). Modes `--check` (mécanisme, CI), `--measure --mode replay|live`.
  - 3 cas gradués `evals/selfeval/BN1-3` (pool `candidates/` + `live/`), `graded_by best_of_n` → skippés par self_eval_debate, mesurés par best_of_n.
  - Cas eval `bestofn_mechanism_picks_max` (fixture) → `run_evals` **19/19**.
  - Mesure LIVE : 9 vrais agents rédacteurs (3 cas × 3), prompts neutres. Scores : BN1 [9,7,6], BN2 [4,4,4], BN3 [6,6,2]. baseline (moyenne) 0,533 → candidate (best-of-N) 0,633.
- **Résultat** : **gain_oriente = 0,10 ≥ seuil 0,03 → best_of_n_enabled=true** (`adoption_gate.json`, decision_source=live). Mesure replay (pool) 0,49 marquée illustrative (variance d'auteur, pas une preuve).
- **Divergence / honnêteté** : décision d'adoption basée sur LIVE (vraie variance), pas sur le pool (que j'écris = gaming). Sample petit (bruit ±0,05). BN2 = variance nulle (best-of-N n'aide pas là). Estimateur gain = mean(max − mean) ≥ 0 par construction ; le bar +0,03 filtre le « assez gros pour payer le coût N× ».

### 2026-07-02 — V2-1b best-of-N : 8 cas, gain=0.1125, câblé Phase 2=oui
- **Prévu** : consolider 3→8 cas, re-mesurer live, câbler en Phase 2 si gain ≥ 0,03.
- **Réalisé** :
  - 5 nouveaux cas gradués BN4-8 (export, scheduler, linter, translator, dedup) — skills ordinaires figés avant mesure, live-only (pas de pool d'auteur). `best_of_n.py` : `run_check` skippe les cas sans pool, nouveau mode `--select` (sélecteur Phase 2).
  - 15 nouveaux agents rédacteurs (prompts neutres). Scores par cas : BN1[9,7,6] BN2[4,4,4] BN3[6,6,2] BN4[2,2,2] BN5[6,4,4] BN6[4,2,2] BN7[6,4,6] BN8[6,8,2]. baseline 0,45 → candidate 0,5625.
  - **gain_oriente = 0,1125 ≥ 0,03 → gate OK → câblage**. SKILL.md Étape 2.4bis (opt-in `--bestofn=on`, N=2, writer-unique : génération // + sélection/écriture sérialisées, ×2 sur la seule §10bis, OFF défaut).
- **Résultat** : best-of-N **consolidé et branché** (opt-in). Le gain tient sur échantillon élargi (2 cas à variance nulle inclus, honnête).
- **Vérifs** : `run_evals` 19/19 · `self_eval_debate --replay` 6/6 · `best_of_n --check` green · SKILL.md 499 lignes (< 500).
- **Honnêteté** : décision sur LIVE (vraie variance), pas sur pool. Cas choisis avant mesure (pas de cherry-pick variance). Estimateur gain = mean(max − mean) ≥ 0 ; le bar +0,03 filtre le « assez gros pour payer ×N ».

### 2026-07-02 — V2-2 ensemble de vérifieurs : 8 cas durs, gain=-0.125, câblé=non
- **Prévu** : tester si 3 vérifieurs cheap (Haiku, vote) égalent/battent le Juge fort (Opus) sur la justesse. Gate +0,03.
- **Piège réglé** : mesurable seulement sur des cas où un vérifieur se trompe parfois → 8 cas de vérification DIFFICILES (verdicts limites CONFIRMÉE↔REJETÉE↔PARTIELLE) à vérité-terrain objective (passage présent/absent), figés avant mesure, 1 cas facile de contrôle.
- **Réalisé** :
  - `scripts/ensemble_verifiers.py` : N=3, vote majoritaire, règle d'égalité figée (3 distincts → PARTIELLE), modes `--check` (CI) / `--measure live|replay`, flag `--ensemble=on` (OFF défaut). Writer-unique (lectures //, agrégation sérialisée).
  - `evals/ensemble/EV1-8` (plan + critique + ground_truth lecture seule). Cas eval `ensemble_aggregation_mechanism` → run_evals 20/20.
  - Mesure LIVE : 32 agents (8 Opus baseline + 24 Haiku). baseline 0,875, candidate 0,75.
- **Résultat** : **gain_oriente = −0,125 < 0 → ensemble_enabled=false, NON câblé** (`adoption_gate_ensemble.json`).
- **Analyse** : cas décisif EV3 (PARTIELLE) — les 3 Haiku font la MÊME erreur (sur-créditent l'idempotence, ratent le rollback absent) → le vote majoritaire amplifie l'angle mort partagé au lieu de le corriger (échec classique de l'ensembling quand les erreurs sont corrélées). Opus tranche juste. EV6 = match nul (GT PARTIELLE discutable, gardée immuable, sans effet sur le gain).
- **Honnêteté** : pas le cas coût (justesse pas égale). Vérité-terrain figée avant mesure, non modifiée après (pas de p-hacking). Décision sur le live.

### 2026-07-02 — V2-2 CORRIGÉ : ensemble 100% Opus (Max flat-rate), gain=0.0, câblé=non
- **Correction** : le 1er run (3 Haiku vs 1 Opus, gain −0,125) était hors-sol — sous forfait Max via Agent SDK, aucun écart de coût entre modèles, donc « vérifieurs cheap » n'a pas de sens. Reformulé en **auto-cohérence** : 3 vérifieurs **Opus** (vote) battent-ils 1 Juge **Opus** ?
- **Réalisé** : 24 vérifieurs Opus (3/cas) sur les mêmes 8 cas durs (vérité-terrain inchangée, immuable). `ensemble_verifiers.py` réorienté (membres `ens_*`, plus de `haiku`), note d'intégrité + cas coût → « efficience ».
- **Résultat** : baseline 1 Opus **0,875** = candidate 3 Opus **0,875** → **gain 0,0 → efficience_a_decider, ensemble_enabled=false**.
- **Analyse** : l'ensemble Opus récupère EV3 (PARTIELLE, correct — là où les Haiku échouaient), mais rate EV6 **exactement** comme le Juge unique (les 4 échantillons Opus indépendants disent CONFIRMÉE). L'erreur EV6 est **systématique** (jugement sur une critique dont le point central tient), pas du bruit → le vote ne l'aide pas. Enseignement : l'auto-cohérence ne paie que sur des erreurs stochastiques ; ici elles sont corrélées. Sous Max, ×3 latence pour 0 gain → garder le Juge unique.
- **Note EV6** : les 4 Opus indépendants disent CONFIRMÉE vs ma vérité-terrain PARTIELLE → ma GT y est probablement trop fine (le point routing-observability tient = CONFIRMÉE défendable). Gardée immuable (pas de p-hacking) ; sans effet sur le gain (match nul).

### 2026-07-02 — V2-3 déclencheur cron hebdo (livré, non enregistré)
- **Prévu** : opérationnaliser le déclencheur de la boucle du §11 (V1 manuel → forme-cible tâche hebdo).
- **Réalisé** :
  - `auto_improve.py --log` : append 1 ligne métadonnées-only à `interactions.jsonl` (data_model §9) à chaque passe — complète le câblage mémoire.
  - `scripts/auto_improve_cron.ps1` : wrapper (cd skill + `python … --log`, log horodaté dans `cron.log` gitignoré).
  - `scripts/register_cron.ps1` : installe/retire (`-Remove`) une tâche utilisateur Windows, dimanche 03:00, **trigger temporel + StartWhenAvailable** (survit à la veille — pattern connu). Pas d'admin.
  - `_mode-plan-meta/CRON.md` : doc install/retrait + limite V1 (mesure+log, pas d'auto-patch sans l'étape LLM).
- **Nature** : trigger/ops, **pas de gate +0,03** (ce n'est pas une capacité). Les deux .ps1 parsent sans erreur.
- **Non enregistré** : l'installation réelle (`register_cron.ps1`) est un changement système → laissée à Sébastien. Vérifs : `auto_improve --log` écrit bien la ligne ; `run_evals` 20/20.

### 2026-07-02 — Anti-régression de la boucle : prouvée (logique) + enforcée (revert)
- **Question (Sébastien)** : comment vérifie-t-on que l'auto-amélioration ne génère pas de régression ?
- **Constat honnête** : le gate triple (capability↑ ET regression==1.0 ET holdout==1.0 / sinon REVERT) était **conçu mais jamais éprouvé** (V1 dry-run, git jamais touché, gate jamais exercé sur un vrai candidat).
- **Comblé** :
  - `auto_improve.py --check` : **prouve** en CI que le gate accepte la vraie amélioration et **bloque** les 4 régressions (capability égale/en baisse, evals<1.0, hold-out<1.0). Cas eval `auto_improve_gate_blocks_regression` → run_evals 21/21.
  - `auto_improve.py --sandbox-apply "<cmd>"` : **enforcement** — applique un candidat en bac à sable git, re-mesure, **`git checkout` si le gate échoue** → l'arbre reste propre, aucun patch régressif ne survit. Exige un arbre propre au départ ; ne committe jamais (gate OK = laissé pour revue humaine).
- **Reste (honnête)** : la GÉNÉRATION du patch (skill-auto-improver, étape LLM) n'est pas dans un script → le sandbox est prêt, mais la boucle complète auto reste un job agentique séparé. Caveats : replay déterministe ne valide pas un changement de prompt d'agent (staleness → à re-mesurer en --live) ; hold-out petit (2 cas).

### 2026-07-02 — V2-4 phase L3 : gate statique (livré + testé)
- **Prévu** : L3 (pousser la frontière du domaine d'un skill stratégique) — cœur buildable = le gate statique anti-hallucination.
- **Réalisé** :
  - `scripts/l3_gate.py` : par trouvaille du labo → `ancrée` (`verify_citations.is_anchored(passage_source, sources.md)`) ET `exprimable` (`cas_de_test_futur` non vide) → `injecter`, sinon `backlog`. Sortie `l3_gate.json` (data_model §8). Modes `--check` / `--run`.
  - `evals/l3/L3_1_nutrition/` : 3 trouvailles — SOL-outil-usda (ancrée+exprimable → injecter), SOL-quantique (passage inventé absent des sources → backlog), SOL-prompt-citation (ancrée mais cas_de_test vide → backlog). Cas eval `l3_gate_mechanism` → run_evals 22/22.
  - `references/l3.md` : doctrine (quand, chaîne, gate 2-temps, contrats, garde-fous). SKILL.md : 2 lignes de table étendues (reste à 500).
- **Scope honnête** : le gate STATIQUE est livré + testé (le filtre exécutable). La chaîne LLM diagnostic-plafonds→labo→application = orchestration (mode-plan spawne, pas de script). Le gate DYNAMIQUE (ré-éval contre le golden du skill cible) = reporté (nécessite le skill construit).
- **Point clé** : anti-hallucination réel — une solution citant un passage absent des sources est backloggée, jamais injectée. Rien n'entre sans son futur cas golden.

### 2026-07-02 — Audit code (3 auditeurs //) + correctifs #1–#7
- **Audit** : 3 agents adversariaux read-only (mesure/eval · sûreté auto_improve+v3.6 · intégrité/cross-platform). Trouvailles vérifiées à la main.
- **Corrigés** :
  - **#1 (CRITIQUE)** `run_evals.py:138` : `python3` en dur → `sys.executable`. Le harnais CI était 100% rouge hors shim (Windows) et neutralisait la boucle (regression=0). **Vérifié : 22/22 SANS shim.**
  - **#2 (MAJEUR)** `sandboxed_apply` : check+revert scopés à `-- .` (cohérents) + `git clean -fd` pour supprimer les fichiers non-suivis créés par un patch (sinon une régression qui ajoute un fichier survivait).
  - **#3 (MAJEUR)** `is_anchored` : seuil `MIN_ANCHOR_WORDS=3` → l'anti-hallucination n'est plus contournable par citation triviale (`"le"` ne s'ancre plus). Vrais passages inchangés.
  - **#4 (MAJEUR)** gate : `< 1.0 - 1e-9` au lieu de `!= 1.0` (robustesse flottante, aucune régression masquée).
  - **#5 (MAJEUR)** `align_critiques` : `score_local: null` coercé en 5 (plus de TypeError).
  - **#6 (MAJEUR)** `--sandbox-apply` : docstring + help signalent `shell=True` = entrée de confiance, PAS une isolation d'exécution.
  - **#7 (MINEUR)** SKILL.md : « 18 golden cases » → sans nombre (fin de la dérive doc↔code).
- **Limites actées (non corrigées, documentées)** : best-of-N gain=dispersion (≥0 par construction) ; hold-out 2 cas (pouvoir faible) ; rubrique/ensemble/l3 sans provenance hash (par conception). À durcir si besoin.
- **Vérif** : run_evals 22/22, self_eval 6/6, _meta_eval + tous les `--check` green — **le tout sans shim python3**.

### 2026-07-02 — Durcissement : hold-out 2→6, apply_exit, 2 doc-lines
- **Hold-out élargi** (le vrai backstop anti-reward-hacking) : +4 cas figés avant mesure, 4 registres — HO3 (H1 absent), HO4 (H8 writer-unique), HO5 (should-not-fire section couverte), HO6 (citation non-ancrée via verify_citations). Vérité-terrain immuable, lecture seule. `self_eval_debate --replay --dir _holdout` → **6/6**. Le gate rejoue déjà le hold-out ; couverture ×3.
- **apply_exit** (intégrité de mesure) : dans `sandboxed_apply`, si `proc.returncode != 0` → statut **APPLY_FAILED** (revert+clean, ni commit ni « pas de gain »). Une panne d'application ne se déguise plus en « la techno n'aide pas ».
- **2 doc-lines** : best_of_n (Goodhart — gain conditionné à la fidélité de la rubrique) ; ensemble (pas de provenance-hash car live-only ; nécessaire si un mode replay/cache est ajouté).
- **Vérif (sans shim)** : run_evals 22/22, self_eval 6/6, hold-out 6/6, _meta_eval + tous --check green. Démos : apply_exit → APPLY_FAILED ; hold-out cassé → revert.
- **Verdict** : harnais propre. (1)/(3) restent documentés-non-corrigés (défendables).

## Bilan V1 (2026-07-01)
Instrument de mesure des agents LLM de mode-plan LIVRÉ et vert de bout en bout :
`self_eval_debate` (replay déterministe, table fermée, STALE_FIXTURE), `verify_citations`,
`_meta_eval` (grader-of-graders 3 polarités), passe H8 d'ablation datée, hold-out anti-gaming,
gate C13, boucle d'auto-amélioration (gate capability/regression/holdout, déclencheur manuel).
Corpus : S1–S8 (4 gradés replay + 4 graded_by), 3 meta-cas, 2 hold-out. 15 evals v3.x intactes.
**V2 (best-of-N réel, ensemble, L3, cron) reste gaté sur +0.03 de capability — non démarré.**
