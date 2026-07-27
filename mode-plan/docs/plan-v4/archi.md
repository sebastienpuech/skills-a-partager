# archi — mode-plan v4.0 (redraft round 2)

> Composants, contrats d'exécution, couche harnais. Tout est opt-in par flag et append-only vs v3.6. V1 = instrument de mesure ; V2 = frontière+ gaté.

---

## 1. Vue d'ensemble

```
Phase 1 ─▶ Phase 2 Draft ─▶ Phase 3 Debate Room ─▶ Phase 4 Patch+Sessions
                                   │  ▲                     │
                        self_eval_debate.py (mesure)   journal.md
                        verify_citations.py            self_diagnosis --selfeval
                        [L3 opt-in = V2]               [best-of-N gate = V2]
```

Le pipeline v3.6 est préservé ; v4.0 greffe des modules **à côté**, sans casser l'existant.

## 2. Composants V1 (l'instrument de mesure)

### 2.1 `scripts/_normalize.py` — fonction canonique partagée (ARCH-003, CRITIQUE)

**Une seule** fonction de normalisation, définie ici une fois, importée par `align_critiques.py` (dedup de sections) ET `verify_citations.py` ET `self_eval_debate.py`. Spec exacte (SIM-004) :

```python
def norm(s: str) -> str:
    # 1. lower()
    # 2. NFKD + suppression des diacritiques (é→e, ç→c)
    # 3. apostrophes typographiques ’ ‘ → '  ; guillemets « » " " → "
    # 4. collapse tout whitespace (\s+) en une espace, strip
    # 5. retire la ponctuation terminale de citation … . , ; :
    return ...
```

Interdit de redéfinir une normalisation ailleurs (le simulateur flaguera un doublon).

### 2.2 `scripts/verify_citations.py` (SIM-004, ARCH-001)

Post-étape déterministe, 0 LLM. **Contrats amont consommés** (ARCH-001) : les JSON des critics (`passage_cite`), de `defenses.json` (`passage_qui_repond`), de `verdict.json` (`passage_verifie`). Pour chaque citation : `norm(citation) in norm(source_file)` ? Absente → `non_ancre` + action de downgrade (CONFIRMÉE→PARTIELLE, ou flag le Défenseur). Sortie : `citations_report.json` (cf. data_model §3).

### 2.3 `scripts/self_eval_debate.py` — CONTRAT D'EXÉCUTION (SIM-002, CRITIQUE)

Le cœur de v4.0. Contrat précis pour être buildable :

1. **Entrée** : un dossier `evals/selfeval/<case>/` (3 .md + `expected.json`).
2. **Invocation des agents** : pour chaque agent requis par le cas, le script lit `references/adversarial/<agent>.md`, le passe comme prompt à un sous-agent `general-purpose` (mécanisme Cowork identique au run normal), avec les 3 .md du cas en entrée. *En CI sans agents* : mode `--replay` qui rejoue des sorties d'agents pré-enregistrées (`evals/selfeval/<case>/recorded/<agent>.json`) → rend le test déterministe et 0-token.
3. **Traduction sortie → pass/fail** : le script parse le JSON de l'agent et évalue `expected_verdicts` du cas (règles binaires : « contient gravité X sur hook Y », « verdict==Z », « aucun TROUVÉ sur critique C »). Chaque règle → true/false.
4. **Should-not-fire** : un cas peut asserter qu'un agent NE flag PAS (S2). Ancrage : si l'agent produit une citation, `verify_citations` vérifie qu'elle pointe une ligne réelle.
5. **Sortie** : `selfeval_report.json` (data_model §2) — score capability, score regression, détail par cas + traces des cas ratés (error-analysis, pas juste le score — H5).

### 2.4 `scripts/_meta_eval.py` — grader-of-graders (HARN-001)

Mini-jeu fixe de 2-3 cas où la **sortie pass/fail de `self_eval_debate.py` est elle-même assertée** contre une vérité connue (ex : un cas dont on SAIT que S1 doit fire ; si le grader dit « pass » alors que l'agent n'a pas fired, le grader est cassé). Sans ça, la couche de mesure n'est pas mesurée.

### 2.5 Passe H8 sur le fan-out hérité (HARN-002) — datée, obligatoire

**Avant** de greffer tout module frontière+ : pour chaque agent hérité (4 critics, Défenseur, Juge, Observateur), une passe d'ablation via le self-golden-set — « si je retire cet agent (ou le remplace par 1 appel fort), le score capability baisse-t-il ? ». Résultat consigné et **daté** dans `_mode-plan-meta/h8_ablation_<date>.md`. Garde l'agent si le score baisse ; sinon, candidat à simplification. C'est la dette de v3.6 qu'on solde.

### 2.6 Durcissement des 3 scripts

`align_critiques.py` : dedup via `norm()` sur les noms de section (rattrape les quasi-doublons). `check_convergence.py` : try/except autour du parse → décision `ERROR` explicite au lieu de crash. `check_regression.py` : détection de langue (FR/EN) + cap sur le nombre d'alertes (défaut 20, triées par gravité).

## 3. Composant L3 — phase opt-in (V2, spécifiée maintenant)

Déclenchée seulement si `type=skill` ET `ambition=stratégique`. Enchaîne l'écosystème existant :

```
diagnostic-plafonds ─▶ labo-recherche ─▶ gate ─▶ application-solutions ─▶ injecté au draft
```

**Résolution du poule-et-œuf du gate (ARCH-004, SIM-005)** : au moment du plan, le skill cible **n'a pas encore** de golden set exécutable. Donc le gate L3 fonctionne en deux temps :
- **À l'instant du plan** : le gate est *statique* — une trouvaille du labo n'entre dans le draft que si (a) elle est ancrée sur une source vérifiable (pas une hallucination) et (b) elle est *exprimable* comme un futur cas du golden set §10bis du skill cible (on écrit le cas de test en même temps que la techno). Sinon → `backlog spéculatif`.
- **Après build du skill cible** : quand son golden set §10bis existe et tourne, la trouvaille est ré-évaluée *dynamiquement* ; si elle ne bat pas la pratique standard, elle est retirée. Le gate L3 n'interroge donc JAMAIS le self-golden-set de mode-plan — il interroge (statiquement puis dynamiquement) le golden set du **skill généré**.

Sur `type=app` ou jetable : sautée.

## 4. Décisions techniques (défauts explicites)

- **Tout opt-in est OFF par défaut** : sans flag, comportement v3.6 strict (PRAG-001, le gating neutralise le risque des modules non construits).
- **Seuil d'adoption unique = +0.03** de score capability (SIM-003). Réutilisé partout (best-of-N, ensembles). Deux décisions distinctes mais **même seuil** : (D1) « activer un module frontière+ ? » et (D2) « garder un agent hérité ? » — les deux lisent `adoption_gate.json`.
- **best-of-N (V2)** : en V1 on ne construit QUE le *gate à sec* — `adoption_gate.json` produit avec un candidat no-op, pour prouver que la mécanique de décision marche avant de câbler la génération réelle.
- **Ensemble de vérifieurs (V2, ARCH-005/PRAG-005)** : concept noté, non construit en V1. Lectures parallèles / agrégation sérialisée (writer-unique) — note de conception, pas de code V1.

## 4bis. Couche Harnais (H2–H8)

- **Context (H3)** : chargement à la demande des 3 fichiers par agent ; progressive disclosure du SKILL.md (≤ 500 lignes, reste en `references/`).
- **Vérification (H2)** : deux niveaux — (a) Debate Room vérifie le plan produit (existant) ; (b) `self_eval_debate.py` vérifie les vérifieurs (nouveau), lui-même vérifié par `_meta_eval.py`. `verify_citations.py` = vérifieur non-gamable des citations.
- **Mémoire (H4)** : `_mode-plan-meta/` (`interactions.jsonl`, `issues.md`, `proposed_fixes.md`) + `journal.md` + `.mode-plan/*.json` rejouables.
- **Observabilité (H5)** : JSON intermédiaires conservés ; `self_eval_debate` logue les traces des cas ratés (error-analysis).
- **Garde-fous (H6)** : caps de round (3), timeouts, flags OFF par défaut, gate de mesure avant adoption, sandbox git (commit/revert), `expected.json` en lecture seule pour le moteur.
- **Outils (H7)** : scripts avec `--help`, sortie JSON, idempotents ; `_normalize.py` partagé (pas de redondance).
- **Fan-out (H8)** : passe d'ablation datée sur le fan-out hérité (§2.5) ; frontière+ gaté ; écritures sérialisées.

## 5. Rétro-compatibilité & flags

`self_diagnosis.py` gagne `--selfeval=on` → **C13** : `evals/selfeval/` existe, `self_eval_debate.py --replay` tourne, `_meta_eval.py` passe. Flags v3.x inchangés. Sans flag → v3.6 strict, 15 evals vertes.

## 6. Sécurité / observabilité

Le moteur ne pousse jamais sur `main` sans regression==100 % ; ne peut pas éditer `expected.json`. Runs de veille : contenu tiers isolé du flux de contrôle. `interactions.jsonl` = métadonnées only. Run raté rejouable depuis `.mode-plan/`.


---

## Patches stratégiques v1.1
> Debate Room round 2 du 2026-07-01. 18 critiques évaluées, 12 confirmées, 3 partielles, 3 rejetées (désaccords de priorité éliminés : PRAG-001/002/003).

### Patch [MAJEUR] — 2.3 `scripts/self_eval_debate.py` — CONTRAT D'EXÉCUTION (SIM-002, CRITIQUE)

**Source** : ARCH-R2-002 (angle : architecte)

**Modification** : 

## 2.3bis. Anti-dérive des fixtures replay (ARCH-R2-002)

Chaque `recorded/<agent>.json` porte une provenance obligatoire :
```json
{ "_provenance": {"agent_file": "references/adversarial/critic-harnais.md",
                   "agent_sha256": "<hash du .md au moment de l'enregistrement>",
                   "recorded_at": "<date>"},
  "output": { ... sortie de l'agent ... } }
```
Au démarrage de `self_eval_debate.py --replay`, le script recalcule le sha256 de chaque `agent_file` référencé et **échoue avec `STALE_FIXTURE`** (pas un pass silencieux) si le hash diffère. Contrat opposable : toute édition d'un prompt d'agent par le moteur DOIT ré-enregistrer les `recorded/` impactés dans le même commit, sinon la CI casse volontairement. La suite regression `--replay` ne peut jamais être verte sur un prompt dérivé.


### Patch [CRITIQUE] — 2.3 self_eval_debate.py — CONTRAT D'EXÉCUTION (point 2)

**Source** : SIM-001 (angle : simulateur)

**Modification** : archi §2.3 → append : recorded/<agent>.json contient EXACTEMENT le JSON brut renvoyé par l'agent live (même schéma consommé en mode live), un fichier par agent nommé <agent>.json (ex : recorded/critic-harnais.json = la sortie complète du critic ; recorded/juge.json = verdict.json ; recorded/defenseur.json = defenses.json). Loader replay et parseur live appellent le MÊME parseur. Committer le dossier recorded/ complet du seed S1 comme référence dans data_model §1.

### Patch [CRITIQUE] — 2.3 self_eval_debate.py — CONTRAT D'EXÉCUTION (point 3)

**Source** : SIM-002 (angle : simulateur)

**Modification** : data_model §1 → append une table FERMÉE « clé expected_verdicts → prédicat » : {contient_gravite:G, sur_hook:H} → ∃ critique tq critique.gravite==G ET critique.hook==H ; {au_moins_une:V} → count(verdict.json.verdicts[].verdict==V) ≥ 1 ; {aucun_trouve_sur:C} → ∄ defense tq defense.critique_id==C ET defense.verdict==TROUVÉ. Règle de composition : cas pass ssi TOUTES les clés de expected_verdicts + tous les should_not_fire passent. Toute clé hors table = erreur de config (fail explicite, jamais pass silencieux).

### Patch [MAJEUR] — 2.3 point 4 (should-not-fire) + spec S2

**Source** : SIM-006 (angle : simulateur)

**Modification** : archi §2.3 point 4 → préciser : should_not_fire PASSE ssi l'agent ne produit AUCUNE critique dont section (après norm) == la section visée, INDÉPENDAMMENT de l'ancrage. verify_citations n'intervient PAS dans la décision should-not-fire ; l'ancrage ne sert qu'aux assertions should-fire (le Défenseur TROUVÉ de S2 doit être ancré). Séparer explicitement les deux chemins de décision dans le contrat.

### Patch [CRITIQUE] — 2.3 self_eval_debate.py

**Source** : HARN-001 (angle : harnais)

**Modification** : Mettre recorded/ sous le meme verrou lecture-seule que expected.json ; stocker un hash du prompt d'agent, la CI echoue si le .md a change sans re-enregistrement ; au moins 1 run --live nocturne/semaine pour re-ancrer.

### Patch [MINEUR] — 4bis Couche Harnais (H6)

**Source** : HARN-004 (angle : harnais)

**Modification** : Ajouter un budget chiffre au self-eval live (max_spawns=50, timeout_total=15min, ou --live limite a 3 cas echantillon, reste en --replay). --live complet reserve au run nocturne.

### Patch [MINEUR] — 2.3 `scripts/self_eval_debate.py` — CONTRAT D'EXÉCUTION (SIM-002, CRITIQUE)

**Source** : ARCH-R2-003 (angle : architecte)

**Modification** : 

## 2.3ter. Séparation invocation / grading dans self_eval_debate (ARCH-R2-003)

Deux fonctions internes à frontière nette (même fichier acceptable, interface explicite obligatoire) :
- `collect_agent_outputs(case_dir, mode) -> dict[agent -> output_json]` : SEULE partie qui connaît live vs `--replay`, le coût token, l'appel sous-agent, la vérif de provenance (§2.3bis). En V2, best-of-N ne modifie QUE cette fonction.
- `grade(case_expected, agent_outputs) -> case_result` : 0 I/O agent, pure ; parse + applique les règles de verdict + should-not-fire (via `verify_citations`). Déterministe, testable seule.
- L'agrégation capability/regression consomme la liste des `case_result`.
Contrat : `grade()` ne doit jamais appeler d'agent ni lire le mode d'exécution. Le grader-of-graders (§2.4) et best-of-N (V2) réutilisent `grade()` inchangée.


### Patch [MINEUR] — 2.4 `scripts/_meta_eval.py` — grader-of-graders (HARN-001)

**Source** : ARCH-R2-004 (angle : architecte)

**Modification** : 

## 2.4bis. `_meta_eval` invoque le grader en boîte noire (ARCH-R2-004)

`_meta_eval.py` **n'a aucune** logique de grade propre. Il pilote `self_eval_debate.py` de bout en bout sur un dossier `evals/selfeval/_meta/<meta_case>/` monté avec des `recorded/` truqués (ex : un `critic-harnais.json` volontairement SANS flag CRITIQUE), puis lit le `selfeval_report.json` RÉEL produit et vérifie que `cases[].pass == expected_grader_verdict`. Ainsi le seul chemin de grading testé est celui de production : impossible qu'un second parseur diverge. `_meta_eval.py` se limite à : (1) préparer le mini-jeu truqué, (2) exécuter `self_eval_debate.py --replay` dessus, (3) comparer le rapport obtenu à `expected_grader_verdict`.


### Patch [MAJEUR] — 2.4 _meta_eval.py

**Source** : HARN-002 (angle : harnais)

**Modification** : Exiger AU MOINS 3 meta-cas couvrant les 3 polarites (no-fire->fail, fire-correct->pass, faux-positif->fail). Vert seulement si les 3 passent.
