# data_model — mode-plan v4.0 (redraft round 2)

> Entités, schémas, contrats. JSON strict, parseable sans LLM. Intègre SIM-001 (seed de référence réel), ARCH-001 (contrats amont), SIM-003 (deux décisions / un seuil).

---

## 1. Plan-graine annoté — `evals/selfeval/<case>/` (SIM-001, CRITIQUE)

Un cas = 3 mini-fichiers de plan RÉELS + `expected.json` + (optionnel) `recorded/` pour le mode replay.

**Au moins un seed complet est commité comme référence.** Exemple canonique `S1_no_golden_set/` :

`spec_produit.md` (le contenu réel, volontairement troué — pas de golden set) :
```markdown
# spec — widget-notif (skill)
## Vision
Un skill qui envoie une notif quand un build casse.
## Persona
Dev solo, déclenchement auto sur webhook CI.
## Fonctions
1. Parser le payload CI. 2. Formatter un message. 3. Envoyer sur Slack.
# (AUCUNE section golden set / signal de succès — trou H1 planté)
```
`archi.md` (réel, minimal) :
```markdown
# archi — widget-notif
## Composants
- parser.py, formatter.py, sender.py
## Garde-fous
- timeout 5s sur l'envoi, retry x2  (section PROPRE = should-not-fire)
```
`data_model.md` (réel, minimal) : `{ build_event: {id, status, branch, commit} }`

`expected.json` (la vérité-terrain, immuable, jamais vue par l'agent testé) :
```json
{
  "case_id": "S1_no_golden_set",
  "type_projet": "skill",
  "agents_requis": ["critic-harnais", "juge"],
  "expected_verdicts": {
    "critic-harnais": {"contient_gravite": "CRITIQUE", "sur_hook": "H1"},
    "juge": {"au_moins_une": "CONFIRMÉE"}
  },
  "should_not_fire": [
    {"agent": "critic-harnais", "fichier": "archi.md", "section": "Garde-fous"}
  ]
}
```

**Construction du corpus** : 1 seed par scénario S1–S8 (§spec 5). Chaque `should_not_fire` avec citation est ancré par `verify_citations`.

## 2. Rapport de self-éval — `self_eval_debate.py` → `selfeval_report.json`

```json
{
  "mode": "live" | "replay",
  "suite": "capability" | "regression",
  "total": 8, "passed": 6, "failed": 2,
  "cases": [
    {"case_id": "S1_no_golden_set", "should_fire": true, "fired": true, "pass": true,
     "regles": [{"agent":"critic-harnais","regle":"contient CRITIQUE sur H1","ok":true}]},
    {"case_id": "S2_already_covered", "should_fire": false, "fired": true, "pass": false,
     "trace": "le critic a flaggé archi.md/Garde-fous (faux positif)"}
  ],
  "score_capability": 0.75, "score_regression": 1.0
}
```

Mode `replay` : lit `recorded/<agent>.json` au lieu d'appeler les agents → déterministe, 0 LLM, CI-ready. Règle de commit d'un patch : `score_capability↑ ET score_regression==1.0`.

## 3. `verify_citations.py` → `citations_report.json` (ARCH-001)

**Contrats amont consommés** (rendus explicites) : `passage_cite` (critiques), `passage_qui_repond` (defenses.json), `passage_verifie` (verdict.json). Normalisation via `_normalize.norm()` (une seule source).

```json
{
  "total_citations": 12, "ancrees": 11,
  "non_ancrees": [
    {"source": "juge", "critique_id": "ARCH-003", "passage": "…",
     "fichier": "archi.md", "action": "verdict CONFIRMÉE → PARTIELLE"}
  ],
  "taux_ancrage": 0.917
}
```

## 4. `journal.md` (par projet) — schéma (PRAG-003 : nice-to-have assumé)

Append-only, bloc « État actuel » glissant en tête (repris de `projet-vivant`).

```markdown
# journal — <nom_projet>
## État actuel  (réécrit en tête à chaque MAJ)
- Phase : <2/3/4> · Sessions : <n>/<N> · Dernier score Debate Room : <x>/10 · Prochain pas : <…>
---
## Log (append-only, daté)
### <date> — <événement>
- Prévu : <…>  Réalisé : <…>  Divergence : <…>
```

## 5. Gate d'adoption — `adoption_gate.json` (SIM-003 : deux décisions, un seuil)

Un **seuil unique** `+0.03`. Deux décisions distinctes le consomment :

```json
{
  "decision_type": "D1_activer_module" | "D2_garder_agent_herite",
  "objet": "best_of_n" | "ensemble_verifieurs" | "critic-simulateur" | "...",
  "baseline_score": 0.72,
  "candidate_score": 0.74,
  "delta": 0.02,
  "seuil_min": 0.03,
  "decision": "rejeter",
  "raison": "delta < seuil ; conserve l'état actuel"
}
```

- **D1** : activer une techno frontière+ (best-of-N, ensemble). `candidate` = avec le module ON.
- **D2** : garder un agent hérité (passe H8, §archi 2.5). `candidate` = SANS l'agent (ablation) ; si le score ne baisse pas de ≥ seuil, l'agent est candidat à simplification.

## 6. Grader-of-graders — `evals/selfeval/_meta/` (HARN-001)

```json
{"meta_case": "grader_detecte_no_fire",
 "input_agent_output": "critic-harnais SANS flag CRITIQUE",
 "expected_grader_verdict": "fail",
 "obtenu": "fail", "ok": true}
```

## 7. Passe H8 — `_mode-plan-meta/h8_ablation_<date>.md`

Tableau : agent | score avec | score sans | delta | décision (garder/simplifier). Daté. Solde la dette de non-mesure de v3.6.

## 8. Contrats L3 (V2)

- `diagnostic_plafonds.json` : `{domaine, plafonds:[{id,type,preuve}]}`
- `labo_findings.json` : `{plafond_id, solutions:[{id,idee,transfert,risque_sur_10,cas_de_test_futur}]}` — noter `cas_de_test_futur` (le futur cas golden du skill cible : c'est le gate statique, archi §3).
- `l3_gate.json` : `{solution_id, ancree:bool, exprimable_en_golden:bool, decision:"injecter|backlog"}`

## 9. Mémoire — `_mode-plan-meta/` (PRAG-006)

- `interactions.jsonl` : 1 ligne/run, **métadonnées only** `{date,nom_projet,type,score_convergence,biais_eleves:[]}`. Le moteur ne le lit PAS pour patcher (il lit issues + golden set).
- `issues.md` : échecs réels + biais ÉLEVÉS de l'Observateur.
- `proposed_fixes.md` : audit trail (patch, delta score, commit/revert).

## 10. Invariants

- Tout `*.json` d'agent tolère des fences markdown (parse robuste).
- `expected.json` immuable pendant un run ; **lecture seule pour le moteur** d'auto-amélioration (ARCH-006).
- Aucune donnée utilisateur brute ni secret stocké.
- Normalisation : une seule fonction (`_normalize.norm`), interdit de la redéfinir.


---

## Patches stratégiques v1.1
> Debate Room round 2 du 2026-07-01. 18 critiques évaluées, 12 confirmées, 3 partielles, 3 rejetées (désaccords de priorité éliminés : PRAG-001/002/003).

### Patch [MAJEUR] — 5. Gate d'adoption — `adoption_gate.json` (SIM-003 : deux décisions, un seuil)

**Source** : ARCH-R2-001 (angle : architecte)

**Modification** : 

## 5bis. Convention de signe du gate (précision ARCH-R2-001)

Le seuil `+0.03` est une **magnitude**, jamais une comparaison brute de `delta`. La règle dépend de `decision_type` :

| decision_type | `candidate_score` = | Adopte / garde SSI | Formule |
|---|---|---|---|
| D1_activer_module | score AVEC module ON | le module fait gagner | `candidate - baseline >= +0.03` |
| D2_garder_agent_herite | score SANS l'agent (ablaté) | l'agent fait perdre (donc utile) | `baseline - candidate >= +0.03` |

Champ obligatoire ajouté au schéma pour lever l'ambiguïté :
```json
{
  "decision_type": "D2_garder_agent_herite",
  "baseline_score": 0.75,
  "candidate_score": 0.74,
  "gain_oriente": 0.01,      // orienté selon la table ci-dessus, toujours comparé >= seuil_min
  "seuil_min": 0.03,
  "decision": "simplifier",  // gain_oriente 0.01 < 0.03 → l'agent n'apporte pas assez
  "raison": "ablation ne coûte que 0.01 < 0.03 : agent candidat à simplification"
}
```
Interdit de comparer `delta` brut : seule `gain_oriente` (toujours `>= seuil_min`) décide, ce qui rend la logique indépendante de la direction du signe.


### Patch [CRITIQUE] — 1. Plan-graine annoté — expected.json

**Source** : SIM-003 (angle : simulateur)

**Modification** : Figer le schéma de sortie commun des critics et y AJOUTER un champ obligatoire "hook": "H1"|"H2"|…|"H8"|null (data_model §10 invariants + archi §2.3). Répercuter dans references/adversarial/critic-*.md pour que la sortie live porte réellement ce champ ; sinon sur_hook reste ininstrumentable et le critère de done §12.1 (attraper une régression H1) n'est pas vérifiable.

### Patch [MAJEUR] — 2 & 5 — règle de commit vs seuil d'adoption

**Source** : SIM-004 (angle : simulateur)

**Modification** : Harmoniser : remplacer §2/§11 par « score_capability augmente de ≥ seuil_min (+0.03) ET score_regression==1.0 » (seuil vraiment unique), OU documenter explicitement pourquoi le commit moteur utilise ↑ strict alors que l'adoption module utilise +0.03 (deux seuils assumés distincts, chacun nommé). Définir la valeur en UN seul endroit source (constante nommée) référée partout.

### Patch [MAJEUR] — 6. Grader-of-graders — evals/selfeval/_meta/

**Source** : SIM-005 (angle : simulateur)

**Modification** : data_model §6 → remplacer input_agent_output (string) par input_recorded: "evals/selfeval/_meta/<case>/recorded/critic-harnais.json" pointant un vrai JSON d'agent (schéma SIM-001) où aucune critique n'a gravite==CRITIQUE. _meta_eval.py invoque self_eval_debate.py --replay sur ce dossier et asserte selfeval_report.cases[].pass==false. Committer ce recorded/ de meta-cas.


---

## Patches d'implémentation v1.2
> Session 2 (2026-07-01) — décisions prises en câblant `verify_citations`.

### Patch [MAJEUR] — 1. Table de dispatch fermée — clé positive `trouve_sur_ancre`

**Source** : implémentation Session 2 (débloque l'assertion S2 reportée depuis Session 1).

**Modification** : la table fermée du §1 (patch SIM-002) ne couvrait que `aucun_trouve_sur` (négatif). Le scénario S2 (§spec 5, §10bis) exige un **Défenseur == TROUVÉ ET citation ancrée** (positif) — inexprimable jusqu'ici. Ajout d'une 5e clé à la table FERMÉE :

- `{trouve_sur_ancre: C}` → ∃ défense tq `critique_id==C` ET `verdict_defense==TROUVÉ` ET `is_anchored(passage_qui_repond, sources)` (via `verify_citations.is_anchored`, fonction PURE — `grade()` reste sans I/O, les sources lui sont passées par `run_case`). C'est le seul point du self-eval où l'ancrage intervient (should-not-fire reste indépendant de l'ancrage — patch SIM-006). Toute clé hors table = fail explicite (inchangé).

### Patch [MINEUR] — anti-staleness = déjà livré en Session 1

**Source** : constat Session 2.

**Modification** : l'item « stocker un hash du .md d'agent dans recorded/, la CI échoue si le .md change » (sessions §2) était déjà réalisé en Session 1 via `_provenance.agent_sha256` + `STALE_FIXTURE` (patch ARCH-R2-002). Session 2 le renforce d'un `.gitattributes eol=lf` pour stabiliser les sha cross-platform. Démontré end-to-end (modif d'un critic → STALE_FIXTURE + exit 1).


---

## Patches d'implémentation v1.3
> Post-V1 (2026-07-01) — findings résolus après la passe H8.

### Patch [MAJEUR] — Table de dispatch fermée — clé `contient_biais` (finding #2)

**Source** : finding H8 (`critic-architecte`, `critic-pragmatiste`, `observateur` non exercés par le corpus).

**Modification** : ajout de 2 cas golden — **S9** (défaut d'archi + scope creep → `critic-architecte` `{contient_gravite:CRITIQUE}` + `critic-pragmatiste` `{contient_gravite:MAJEUR}`, prédicat existant) et **S10** (biais de Debate Room → `observateur`). L'Observateur a un schéma distinct (`biais_detectes[]`, pas `critiques[]`) → 6e clé à la table FERMÉE :

- `{contient_biais: B, gravite: G}` → ∃ biais tq `id==B` ET `detecte==true` ET `gravite==G` dans la sortie de l'Observateur.

Effet : la passe H8 passe de 3 agents `non_exerce` à **7/7 `garder`** — chaque agent hérité est désormais mesuré. Toute clé hors table = fail explicite (inchangé).

### Patch [MAJEUR] — `score_convergence_raw` (finding #1)

**Source** : finding méta (score borné à 0 → faux PLATEAU par saturation).

**Modification** : le Juge émet `score_convergence_raw` (formule non bornée) à côté de `score_convergence` (clampé [0,10]). `check_convergence.py` calcule le delta PLATEAU sur le brut (fallback clampé si absent → rétro-compat). Fixture `convergence_plateau_vs_saturation`.
