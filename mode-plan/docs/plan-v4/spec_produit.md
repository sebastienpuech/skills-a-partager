# spec_produit — mode-plan v4.0 « Dépasser la frontière »

> Plan produit par mode-plan sur lui-même (dogfooding). Redraft round 2 : intègre les 12 critiques CONFIRMÉES + 8 PARTIELLES de la Debate Room round 1.
> Type : skill (itération sur v3.6). Déclenchement manuel. Adversarial : oui.

---

## 0. Règles de fer (immuables)

- **mode-plan ne se réécrit JAMAIS en cours de run.** La consolidation du SKILL.md est un job séparé (skill-auto-improver, hors run).
- **Patches append-only.** Jamais de réécriture destructive d'un fichier de plan ou d'un agent.
- **Le self-golden-set est le prérequis de tout.** Aucune technique « frontière+ » (best-of-N, ensemble de vérifieurs, phase L3) n'est adoptée sans qu'il prouve un gain mesuré. **Corollaire de séquençage** : V1 construit *l'instrument de mesure* ; V2 ajoute les techniques frontière+ *gatées sur cet instrument*.
- **Pas de nouvel agent LLM sans preuve** (test H8). **Et** : le fan-out DÉJÀ hérité de v3.6 (4 critics, Défenseur, Juge, Observateur) doit subir sa propre passe H8 d'ablation avant qu'on greffe quoi que ce soit — sinon on empile sur du non-mesuré.
- **Un labo (labo-recherche) ne se lance qu'après un plafond PROUVÉ + un instrument de mesure.** diagnostic-plafonds d'abord.
- **Rétro-compatibilité dure.** Les 15 evals v3.x restent vertes. Tout nouveau gate est opt-in par flag.

## 0bis. Pré-requis / arborescence de départ (SIM-006)

Le plan s'exécute contre le repo du skill v3.6 existant. Arborescence de départ supposée :

```
mode-plan/                     # le skill v3.6, point de départ
  SKILL.md
  references/adversarial/*.md  # 6 agents (réutilisés tels quels par le self-eval)
  references/harnais.md
  scripts/*.py                 # 5 scripts (3 à durcir)
  evals/evals.json + fixtures/ # 15 golden cases v3.x (deviennent la suite regression)
```

Cibles nouvelles créées par v4.0 : `evals/selfeval/` (corpus + expected), `scripts/self_eval_debate.py`, `scripts/verify_citations.py`, `scripts/_normalize.py` (fonction canonique partagée), `_mode-plan-meta/` (mémoire). Aucune écriture hors de ces chemins.

---

## 1. Vision (1 phrase)

mode-plan v4.0 donne enfin à mode-plan un **instrument pour se mesurer lui-même** (self-golden-set sur ses agents LLM + vérifieur de citations), puis, *une fois cet instrument en place*, pousse au-delà de la frontière sur trois couches — ses mécaniques (L1), le harnais qu'il impose (L2), le domaine du skill généré (L3) — chaque poussée conditionnée à un gain mesuré.

## 2. Problème (pourquoi v4.0) — 4 trous confirmés par double audit

1. **mode-plan est aveugle sur lui-même** : ses evals ne testent que les scripts, jamais ses agents LLM. Un décalage de calibration passe inaperçu → un plan sort avec des trous non détectés.
2. **Citations non vérifiées** : Défenseur/Juge citent des passages ; rien ne vérifie qu'ils existent. Viole son propre H2.
3. **Frontière figée** : doctrine instantanée, sans intake de recherche fraîche ni push domaine.
4. **Suivi dispersé** : pas de journal vivant du plan.

## 3. Persona / usage

Sébastien, déclenchement **manuel**. Triggering/description **hors-scope**. Progressive disclosure **dans le scope** (context engineering).

## 4. Périmètre — V1 (build) vs V2 (backlog gaté)  ⟵ réponse au Pragmatiste

**V1 CORE (ce qu'on construit d'abord — l'instrument de mesure) :**
- Le self-golden-set + `self_eval_debate.py` (teste enfin les agents LLM). [L1]
- `verify_citations.py` + fonction de normalisation canonique partagée. [L1]
- Meta-vérification du grader (grader-of-graders). [L1]
- Passe H8 d'ablation sur le fan-out hérité de v3.6 (datée, obligatoire). [L1]
- Durcissement des 3 scripts fragiles + `self_diagnosis --selfeval=on` (C13). [L1]
- Doctrine harnais mise à jour avril 2026 (3-agents + context-resets) + progressive-disclosure check. [L2]

**V2 BACKLOG (spécifié ici, construit APRÈS que le self-golden-set mesure) :**
- best-of-N (le *gate* est validé « à sec » en V1 ; la génération réelle attend V2). [L1]
- Ensemble de vérifieurs cheap (concept noté, non construit en V1 — PRAG/ARCH-005). [L1]
- Phase L3 opt-in (scan-frontière domaine). [L3]
- Déclencheur cron hebdo (V1 : lancement manuel du moteur ; cron = forme-cible). [PRAG-002]

Raison du séquençage : on ne peut prouver qu'une technique frontière+ dépasse la frontière qu'avec l'instrument de V1. Construire V2 avant V1 = optimiser à l'aveugle.

## 5. Scénarios golden (comportement de mode-plan v4.0)

Jamais chargés dans un run ; ils alimentent le self-golden-set (§10bis).

- **S1 (should-fire)** — plan sans golden set → `critic-harnais` flag CRITIQUE + Juge CONFIRMÉE.
- **S2 (should-not-fire, ancré)** — plan dont une section couvre déjà une critique → Défenseur == TROUVÉ. Assertion ancrée : la citation du Défenseur DOIT pointer une ligne réelle de la section (vérifiable par `verify_citations`), pas un jugement LLM seul (HARN-003).
- **S3 (citation)** — critic cite un passage absent → `verify_citations` == `non_ancre`, downgrade.
- **S4 (refus)** — projet 1-critère → mode-plan refuse de sur-planifier.
- **S5 (L3 gating, V2)** — skill stratégique → L3 déclenchée ; app jetable → sautée.
- **S6 (best-of-N gating)** — best-of-N sans gain golden → `best_of_n_enabled=false`.
- **S7 (writer unique)** — patch draft propose des écritures parallèles → `critic-harnais` (H8) flag.
- **S8 (anti-gaming, hold-out)** — un patch qui monte le score golden mais casse un cas hold-out réel → rejeté (HARN-004).

## 6. Hors-scope v4.0

Triggering ; réécriture consolidée du SKILL.md ; L3 sur projets jetables ; refonte des patterns d'orchestration existants.

---

## 10bis. Harnais & signal de succès (H1) — le self-golden-set

Porte sur les **agents LLM** (nouveauté) ET les scripts (existant). Construction : des plans-graines annotés (trous plantés + sections propres) ; on rejoue la Debate Room et on vérifie les verdicts attendus.

**Complétude & ancrage (HARN-003)** : au moins **un plan-graine de référence complet** est commité (contenu réel des 3 .md, cf. data_model §1) — pas seulement une description. Chaque assertion should-not-fire est **ancrée** (pointe une ligne réelle), jamais laissée à un juge LLM seul.

| Sortie vérifiée | Assertion binaire | Vérifieur |
|---|---|---|
| critic-harnais sur S1 | flag CRITIQUE sur H1 présent | parse JSON du critic |
| Défenseur sur S2 | verdict==TROUVÉ ET citation ancrée | parse defenses.json + verify_citations |
| Juge sur S1 | ≥1 CONFIRMÉE | parse verdict.json |
| Citation inventée S3 | flag==non_ancre | verify_citations.py |
| Projet 1-critère S4 | aucun dossier créé | check FS |
| best-of-N sans gain S6 | best_of_n_enabled==false | lit adoption_gate.json |

**Deux suites** : *capability* (S1–S8, pass-rate bas au départ) vs *regression* (15 golden v3.x + cas capability saturés, ~100 %).

**Grading** : grade-the-output ; partial credit ; should-fire ET should-not-fire ; **non-gamable** — essai en env propre, aucun accès de l'agent testé à `expected.json`.

**Grader-of-graders (HARN-001)** : `self_eval_debate.py` est lui-même sous assertion — un mini-jeu fixe où sa sortie pass/fail est vérifiée contre une vérité connue (cf. archi §4ter). Sinon la couche de mesure n'est elle-même pas mesurée.

---

## 11. Boucle d'auto-amélioration (skill)

| Pièce | Définition |
|---|---|
| **Signal rejouable** | le self-golden-set §10bis |
| **Mémoire** | `_mode-plan-meta/interactions.jsonl` (log analytique, métadonnées only) + `issues.md` (échecs réels + biais ÉLEVÉS de l'Observateur) + `proposed_fixes.md` (audit trail) |
| **Moteur** | `skill-auto-improver` : **lit uniquement issues.md + golden set** (PRAG-006) → patch d'un prompt d'agent ou d'un script → commit si capability↑ ET regression==100 % / revert sinon |
| **Déclencheur** | V1 : lancement **manuel**. Forme-cible : tâche planifiée hebdo (PRAG-002) |
| **Intake frontière** | `veille-test-preuve` ajoute des cas *capability* frais à tester avant adoption |
| **Anti-gaming — hold-out opérationnel (HARN-004)** | un sous-ensemble de cas réels est **tenu hors** du golden set d'optimisation ; un patch qui monte le score golden mais casse le hold-out est rejeté. Surveille la généralisation hors-distribution, pas seulement le score. |
| **Frontière moteur/corpus (ARCH-006)** | séparation dure imposée par l'archi : le moteur ne peut pas éditer `evals/selfeval/expected.json`. Le fichier attendu est en lecture seule pour le moteur. |

**Règle** : mode-plan ne se réécrit pas en run. L'auto-amélioration est un job séparé nourri par la mémoire.

## Mémoire du skill

mode-plan v4.0 persiste sa mémoire dans `_mode-plan-meta/` : `interactions.jsonl` (log analytique, métadonnées only), `issues.md` (échecs réels + biais ÉLEVÉS de l'Observateur), `proposed_fixes.md` (audit trail des patches commit/revert). La boucle du §11 consomme `issues.md` + le golden set.

## 12. Critères de succès de v4.0 (definition of done — V1)

1. `self_eval_debate.py` tourne, exécute S1–S8, et **attrape ≥ 1 régression plantée** sur les agents LLM.
2. Le **grader-of-graders** passe (la mesure est elle-même mesurée).
3. La **passe H8 d'ablation** sur le fan-out hérité est exécutée et datée (garde ou simplifie chaque agent sur preuve).
4. `verify_citations.py` ramène les citations non-ancrées à ~0 sur un run réel.
5. Les **15 evals v3.x restent vertes** ; `self_diagnosis --selfeval=on` (C13) passe.
6. `journal.md` généré (nice-to-have assumé pour un skill mono-fenêtre — PRAG-003, mais utile ici car v4.0 est multi-sessions).


---

## Patches stratégiques v1.1
> Debate Room round 2 du 2026-07-01. 18 critiques évaluées, 12 confirmées, 3 partielles, 3 rejetées (désaccords de priorité éliminés : PRAG-001/002/003).

### Patch [MINEUR] — 12. Criteres de succes (DoD V1)

**Source** : PRAG-004 (angle : pragmatiste)

**Modification** : spec §12 → retirer journal.md de la liste DoD numerotee (le laisser hors-DoD, section separee 'livrables optionnels'). Trancher : soit DoD, soit nice-to-have. Retirer du diagramme pipeline archi §1 tant qu'il n'est pas un livrable ferme.

### Patch [MAJEUR] — 11 hold-out anti-gaming

**Source** : HARN-003 (angle : harnais)

**Modification** : Ajouter evals/selfeval/_holdout/ (meme schema, dossier separe, lecture seule pour le moteur, jamais dans la boucle d'optimisation). Le moteur rejoue holdout apres chaque patch ; regression_holdout<100% -> revert auto.
