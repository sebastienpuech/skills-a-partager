---
name: mode-plan
description: Force la production d'un plan rigoureux en 4 fichiers markdown (spec_produit, archi, data_model, sessions_claude_code) pour tout projet complexe (app, software, skill multi-agent, doc structuré), avec Debate Room adversariale (3 critics parallèles + Défenseur + Juge) et génération de prompts Claude Code self-contained. Utiliser dès que l'utilisateur veut démarrer un nouveau projet complexe, faire un plan d'attaque, planifier un développement multi-sessions, structurer une refonte avant d'implémenter, méthode Cherny, mode plan, plan rigoureux, fais-moi un plan, on planifie d'abord, avant de coder, comme pour le projet Coach, les 4 fichiers. Le skill produit le plan, le challenge, et génère les prompts CC — il ne code rien. Le plan intègre une couche harnais (golden set/signal de succès, vérification, garde-fous, observabilité, mémoire). NE PAS utiliser pour projet simple (≤3 sessions anticipées, pas de golden set), itération sur un projet en cours, ou exécution effective des sessions.
---

# Mode Plan v3.6 — Plan rigoureux Harnais-Aware (Debate Room + Refinement Loop + Méta-cognitif)

Ce skill produit un plan en 4 fichiers markdown pour un projet complexe, le fait challenger par une **Debate Room** (4 critics parallèles + Défenseur + Juge), patche les trous **confirmés** (faux négatifs éliminés), et génère les prompts Claude Code de chaque session. **Le skill ne code rien.** Il s'arrête au handoff CC.

Inspiré de la méthode appliquée intuitivement au projet Coach (`spec_produit.md` + `archi.md` + `data_model.md` + `sessions_claude_code.md`).

**Changements v3.0 vs v2.0** : Phase 3 est maintenant une Debate Room (Pattern 1 d'orchestration-patterns) au lieu d'un critic composite mono-agent ; Phase 2 est enrichie par les patterns extraits de plans réussis (chaînage avec `pattern-extractor`) ; self-diagnosis convertie en circuit-breakers Python (`scripts/self_diagnosis.py`) ; check de non-régression entre versions de patches (`scripts/check_regression.py`).

**Nouveau en v3.3 (Harnais-Aware)** : tout plan intègre désormais une couche **harnais** de bout en bout, fondée sur l'état de l'art 2025-2026. Concrètement : un **4e critic `harnais`** (Red Team, grille H1–H8) dans la Debate Room ; des **sections harnais dans les 3 templates** (signal de succès/golden set au `spec`, Couche Harnais à l'`archi`, session de vérification aux `sessions`) ; une **doctrine `references/harnais.md`** ; et une **gate `self_diagnosis.py --harness=on`** (check C10). Principe : on cesse de planifier *comment l'agent pense* (orchestration, que le modèle absorbe) pour planifier *ce qu'il voit, peut faire, et peut vérifier* (harnais).

**Nouveau en v3.4 (harnais durci)** : la doctrine `references/harnais.md` et le `critic-harnais` intègrent l'état de l'art le plus récent (Q4 2025–Q2 2026) — **anti-gaming** (revers du RLVR : un grader gamable est un faux signal, fondu dans H2/CRITIQUE), **split capability/regression** + grade-the-output au `spec` §10bis, **token-efficience des outils** (chargement différé / exécution par code, H7), **règle du writer unique** (lectures parallèles, écritures single-threaded, H8) et **error-analysis** (lire les traces, pas seulement le score, H5). Aucun changement des scripts ni de la grille H1–H8 — les evals restent vertes (11/11).

---

## Quand mode-plan est pertinent (grille de détection)

Critères binaires :

1. Le projet anticipe **plus de 3 sessions Claude Code** d'implémentation ?
2. Il y a **plusieurs composants ou agents** qui doivent collaborer ?
3. Il existe un **golden set de scénarios testables** ?
4. Il y a des **décisions d'architecture** à figer avant de coder ?

**Au moins 2 critères positifs → mode-plan est justifié.**

**0-1 critère → projet trop simple.** Réponse à l'user :
> "Trop simple pour mode-plan (≤1 critère sur 4). Pas besoin de plan formel — attaque direct en chat ou Claude Code. Si tu veux quand même, dis-le et on continue."

---

## Gotchas (pièges connus à connaître AVANT d'invoquer)

- **Verdict "go" du premier coup = suspect** sur v2.0 (mono-critic). Sur v3.0 (Debate Room), un "go" direct est plus crédible mais reste rare — re-vérifier que le Juge a bien CONFIRMÉ/REJETÉ chaque critique en citant la source.
- **Phase 1 chat libre < 50 mots → plan générique garanti.** Forcer l'user à étoffer.
- **Mode `iterate_existing` requiert fichiers en bon format.** Sections numérotées, headers cohérents. Format custom → critics hallucinent.
- **Append-only patches font grossir les fichiers.** Au-delà de v1.5 sur un même fichier, proposer une consolidation vN.0.
- **Sub-agent custom = pas invocable par nom en Cowork.** Toujours passer le contenu du fichier `.md` comme prompt au `subagent_type: general-purpose`.
- **3 critics parallèles peuvent converger sur le même patch** (mode collapse cross-agents) — c'est OK, le script `align_critiques.py` détecte les doublons et le Défenseur les traite une seule fois.
- **Si tu invoques un MCP tool : nom fully qualified obligatoire.** `server_name:tool_name`. Sans namespace → "tool not found" silencieux.
- **Pattern injection (Phase 2) est optionnelle** — si `outputs/_mode-plan-meta/patterns-from-real-plans.md` n'existe pas, on dégrade vers le draft from template, sans bloquer.

---

## Workflow en 4 phases

```
Phase 1 — Élicitation (3 tours AskUserQuestion + chat libre)
      ↓
Phase 2 — Draft du plan (3 .md, enrichi par patterns réels si dispo)
      ↓
Phase 3 — DEBATE ROOM (4 critics ∥ : archi · prag · sim · harnais → align → Défenseur → Juge)
      ↓
Phase 4 — Patch v1.1 (uniquement CONFIRMÉE + PARTIELLE) + sessions CC
          + check anti-régression + self-diagnosis Python (--harness=on)
```

---

## Phase 1 — Élicitation

### Étape 1.0 — Mode fast-track (optionnel)

Si l'user dit "fast track", "skip questions", "vite", appliquer ces défauts :

```
type: app/software        |  ambition: robust        |  adversarial: oui
point_de_depart: from scratch  |  deadline: moyen   |  stack: à recommander
golden_set: à construire  |  target: local
mémoire (si skill): complet   |  pattern (si skill): à recommander
```

Sauter les Tours 1-3, aller à 1.4. Confirmer : "Mode fast-track : défauts appliqués sur structure, brief libre pour vision/règles/nom."

### Étape 1.1-1.3 — 3 tours AskUserQuestion

**Tour 1 (cadrage projet)** : Q1 type / Q2 point de départ / Q3 ambition / Q4 adversarial.

**Tour 2 (contraintes & livraison)** : Q5 deadline / Q6 stack / Q7 golden set / Q8 target.

**Tour 3 conditionnel** :
- Si Q1=skill : Q9 mémoire / Q10 pattern d'orchestration
- Si Q1=app : Q9 interface UI / Q10 persistance
- Si Q1=doc : Q9 format livraison / Q10 public cible

Détail complet des choix dans `references/workflow.md`.

*v3 : "app/software" pleinement supporté. Pour "skill" et "doc" : dégradation contrôlée avec warning.*

### Étape 1.4 — Brief libre (raccourci)

Après les 3 tours, demander en chat :
> 1. **Vision en 1 phrase** : à quoi sert le projet, pour qui.
> 2. **Règle(s) de fer** : contraintes immuables.
> 3. **Nom court du projet** (snake_case, pour le dossier).

### Étape 1.5 — Récap & validation explicite

Présenter un récap structuré (8-12 lignes) avec tous les Q1-Q10 + vision + règles + nom_projet, puis :
> Je drafte sur cette base ? (oui / corriger X / ajouter Y)

**Ne pas avancer sans un "oui" explicite.**

---

## Phase 2 — Draft du plan (avec injection de patterns)

### Étape 2.1 — Créer le dossier de sortie

```
outputs/<nom_projet>/
```

Si existe déjà et pas `iterate_existing` → demander confirmation.

### Étape 2.2 — Charger les patterns de plans réussis (si dispo)

```python
patterns_file = Path("outputs/_mode-plan-meta/patterns-from-real-plans.md")
if patterns_file.exists():
    # Vérifier nombre de plans source (cf. garde-fou G1 dans pattern-injection.md)
    inject = extract_core_patterns_and_decision_rules(patterns_file)
    drafter_context += f"\n## Patterns from successful plans\n{inject}"
else:
    # Dégradation gracieuse — pas de blocage
    log("v3 pattern injection skipped (no patterns file)")
```

Détail : `references/pattern-injection.md` (garde-fous G1/G2/G3, format attendu, rafraîchissement).

### Étape 2.3 — Lire le template approprié

Lire `references/templates/app/` (seul type templaté en v3). 4 fichiers à produire :
- `spec_produit.md` (vision, persona, scénarios golden set, critères)
- `archi.md` (composants, flux, décisions techniques)
- `data_model.md` (entités, contrats, schéma)
- `sessions_claude_code.md` (généré en Phase 4 après review)

### Étape 2.4 — Drafter les 3 premiers fichiers

Écrire `spec_produit.md`, `archi.md`, `data_model.md` dans `outputs/<nom_projet>/` en suivant les templates + injection patterns si dispo. Substantiel mais imparfait — la Debate Room va challenger.

**(v3.3) Couche harnais à remplir réellement** : lire `references/harnais.md`, puis renseigner pour de vrai les sections harnais des templates — `spec_produit.md` §10bis (golden set + assertions = signal de succès, H1) et `archi.md` §4bis (Couche Harnais, H2–H7). Les laisser en placeholder = la gate C10 bloquera la livraison.

**NE PAS produire `sessions_claude_code.md` à cette étape.**

### Étape 2.5 — Si type=skill : section Mémoire obligatoire

Si `Q1=skill` ET `Q9 ∈ {complet, issues_only}`, `spec_produit.md` DOIT contenir une section "Mémoire du skill" et `archi.md` DOIT décrire les 3 fichiers de stockage (`memory/interactions.jsonl`, `memory/issues.md`, `memory/proposed_fixes.md`). Spec minimale détaillée dans `references/workflow.md` section "Mémoire du skill".

### Étape 2.6 — Mode `iterate_existing`

Si `Q2 = plan existant` : lire les 3 fichiers fournis, skipper le draft, passer en Phase 3.

---

## Phase 3 — Debate Room + Refinement Loop (Pattern 6, v3.2)

Architecture (Pattern 6 d'orchestration-patterns = Debate Room + Refinement Loop) :

```
BOUCLE round R (max 3) :
  3.1  PARALLÈLE :
         Spawn critic-architecte   → .mode-plan/critique_arch_R.json
         Spawn critic-pragmatiste  → .mode-plan/critique_prag_R.json
         Spawn critic-simulateur   → .mode-plan/critique_sim_R.json
         Spawn critic-harnais      → .mode-plan/critique_harnais_R.json   (v3.3)
  3.2  SCRIPT : align_critiques.py → .mode-plan/aligned_critiques_R.json
  3.3  SÉQUENTIEL : Spawn Défenseur (reçoit aligned + 3 fichiers patchés-jusqu'à-vN-1)
                                    → .mode-plan/defenses_R.json
  3.4  SÉQUENTIEL : Spawn Juge      → .mode-plan/verdict_round_R.json
  3.5  SCRIPT : check_convergence.py → décision
       - CONVERGED / NO_ISSUES / PLATEAU / MAX_ITERATIONS → BREAK (sortie de boucle)
       - CONTINUE → appliquer patches v1.R, puis R++ et retour 3.1

3.6  SÉQUENTIEL (post-loop, optionnel) : Spawn Observateur méta-cognitif
                                          → .mode-plan/meta_analysis.json
```

### Étape 3.1 — Spawn 4 critics en parallèle

Spawner **4 sous-agents en parallèle** (Task tool, `subagent_type: general-purpose`), chacun avec un des fichiers :
- `references/adversarial/critic-architecte.md` → `critique_arch.json`
- `references/adversarial/critic-pragmatiste.md` → `critique_prag.json`
- `references/adversarial/critic-simulateur.md` → `critique_sim.json`
- `references/adversarial/critic-harnais.md` **(v3.3)** → `critique_harnais.json`

Input passé à chaque critic : brief consolidé Phase 1 + 3 fichiers du plan concaténés.

**Important** : les 4 spawns doivent être dans un **seul message multi-tool-call** pour vraie parallélisation. Sinon = séquentiel coûteux.

*Dégradation : si le projet est trivial (1-2 critères de détection), le `critic-harnais` peut être calibré léger (H5/H6 en MINEUR). Mais H1 (signal de succès) et H2 (vérification) restent exigés dès qu'il y a un golden set.*

Créer le dossier `outputs/<nom_projet>/.mode-plan/` pour les artefacts intermédiaires.

### Étape 3.2 — Merge déterministe (Python)

```bash
python3 scripts/align_critiques.py outputs/<nom_projet>/.mode-plan/
```

Le script :
- Charge les 3 JSON requis + `critique_harnais.json` **(v3.3, optionnel)** (tolère les fences markdown autour)
- Aligne les critiques avec IDs cross-référençables
- Détecte les doublons inter-angles (même fichier + section)
- Calcule `score_global_pondéré` : **si harnais présent** → 30% archi + 25% prag + 25% sim + 20% harnais ; **sinon** → 40/30/30 (rétro-compatible v3.2)
- Sort `aligned_critiques.json` + `align_summary.txt`

Si un des 3 JSON ne parse pas → relancer ce critic une fois avec l'erreur. Si re-échec → continuer avec 2 critics, marquer `degraded: 1 angle missing` dans le verdict final.

### Étape 3.3 — Spawn Défenseur

Spawn 1 sous-agent avec `references/adversarial/defenseur.md` comme prompt. Input :
- `aligned_critiques.json`
- Les 3 fichiers du plan (texte intégral)

Le Défenseur produit `defenses.json` : pour chaque critique, "le sujet est-il déjà adressé dans le plan ?" (TROUVÉ / PARTIEL / PAS_TROUVÉ + citation).

**C'est l'élimination des faux négatifs.** Sans ce passage, on appliquerait des patches sur des sujets déjà traités → bruit append-only.

### Étape 3.4 — Spawn Juge

Spawn 1 sous-agent avec `references/adversarial/juge.md`. Input :
- `aligned_critiques.json`
- `defenses.json`
- Les 3 fichiers du plan source

Le Juge **relit la source** (pas la rhétorique des autres agents) et tranche chaque paire : CONFIRMÉE / REJETÉE / PARTIELLE. Calcule `score_convergence` (départ 10, -2 par CRITIQUE confirmée, -1 par MAJEUR, -0.3 par MINEUR, -0.5 par PARTIELLE).

Output : `verdict.json` avec `verdicts[]`, `statistiques`, `verdict_global` ∈ {go, patch_required, major_revision}.

### Étape 3.4bis — Vérification des citations (v4.0, Python, déterministe)

**Post-étape après le Juge, 0 LLM** (mode-plan v4.0, archi §2.2). Le Défenseur et le Juge citent des passages du plan ; rien ne vérifiait qu'ils existent (violait le propre H2 de mode-plan). Lancer :

```bash
python3 scripts/verify_citations.py --sources <dir_du_plan> --artifacts outputs/<nom_projet>/.mode-plan/
```

`verify_citations.py` normalise via `_normalize.norm` (source unique) et vérifie que chaque `passage_cite` (critics) / `passage_qui_repond` (defenses) / `passage_verifie` (verdict) est bien ancré dans la source réelle. Sortie `citations_report.json` (data_model §3). **Actions de downgrade** consommées avant d'appliquer les patches (Étape 4.1) : une citation `non_ancre` du Juge rétrograde son verdict (CONFIRMÉE → PARTIELLE) ; une du Défenseur invalide son TROUVÉ (faux négatif ré-ouvert). Sur Windows, invoquer avec `python` (le `python3` du système peut être un stub cassé).

### Étape 3.5 — Check de convergence (Python, déterministe)

À la fin de chaque round, lancer :

```bash
python3 scripts/check_convergence.py outputs/<nom_projet>/.mode-plan/ \
    --max-iterations=3 --threshold=8.0 --plateau-delta=0.5
```

Le script lit tous les `verdict_round_*.json` du dossier et retourne une décision :
- **CONVERGED** : score ≥ 8 (avec 0 confirmé idéalement) → sortie de boucle, livraison
- **NO_ISSUES** : 0 confirmé + 0 partiel → sortie, livraison
- **PLATEAU** : delta de score < 0.5 entre 2 rounds → sortie, livraison (le score ne bouge plus)
- **MAX_ITERATIONS** : 3 rounds atteints sans convergence → sortie, livraison avec warning
- **CONTINUE** : appliquer patches du round courant en append-only `## Patches stratégiques v1.R`, puis R++ et retour à 3.1

Entre 2 rounds : appliquer les patches CONFIRMÉE + PARTIELLE du round R aux 3 fichiers du plan AVANT de relancer 3.1. Le round R+1 voit donc le plan déjà patché et ne re-flag (normalement) pas les mêmes sujets.

**Major_revision (verdict_global du Juge)** : si après round 1, le Juge dit "major_revision" (>2 CRITIQUE confirmées), avertir l'user, présenter les problèmes, demander si on continue la boucle ou si on retourne en Phase 2 redrafter. Cap : max 2 retours en Phase 2, au-delà handoff manuel.

### Étape 3.6 — Méta-cognitif (Observateur, optionnel mais recommandé)

Après la boucle (ou la première sortie), spawn 1 sous-agent avec `references/adversarial/observateur.md`. Input : tous les JSON intermédiaires (critiques_R, defenses_R, verdict_round_R pour le dernier R).

L'Observateur ne reviewe PAS le plan — il observe COMMENT les 5 agents précédents ont raisonné, et détecte 8 biais structurels (mode collapse cross-agents, anchoring sectoriel, Défenseur indulgent, Juge rubber-stamp, etc.).

Output : `meta_analysis.json` avec biais détectés + `score_qualite_debate_room` (0-10) + recommandations de calibration des prompts. Les biais de gravité ÉLEVÉE alimentent `outputs/_mode-plan-meta/issues.md` (mémoire de mode-plan sur lui-même).

**Quand le skipper** : projets simples (1 round CONVERGED direct, < 3 critiques au total) — le méta-cognitif n'a rien à analyser.

### Étape 3.7 — Timeout et fallback dégradé

- Si un critic ne répond pas après ~3 min → continuer avec les 2 autres (marquer `degraded: 1 angle missing` dans le round courant). Pas de re-spawn.
- Si 2 ou 3 critics fail → **mode dégradé v2** : fallback sur `references/adversarial/critic-composite.md` (legacy mono-critic). Marquer : "⚠ Debate Room v3 indisponible round R, fallback composite."
- Si la boucle est en MAX_ITERATIONS avec score < 6 → considérer comme "Debate Room non concluante", marquer le plan livré avec un warning explicite en haut de chaque fichier.
- Si check_convergence.py échoue (verdict.json malformé) → sortir de la boucle en mode safe, livrer ce qui existe.

### Étape 3.8 — Mode `skip review`

Si Q4 = "skip", ne pas lancer la Debate Room. Ajouter en haut de chaque fichier :
```markdown
> ⚠ **PLAN NON CHALLENGÉ** — adversarial review skippée à la demande.
> Risques non identifiés possibles.
```

---

## Phase 4 — Patch + génération sessions_claude_code.md + diagnostic Python

### Étape 4.1 — Appliquer les patches CONFIRMÉE + PARTIELLE en append-only

Pour chaque verdict ∈ {CONFIRMÉE, PARTIELLE} dans `verdict.json`, append au fichier ciblé :

```markdown

---

## Patches stratégiques v1.1

> Issus de la Debate Room v3.0 du <date>. <N> critiques évaluées, <M> confirmées, <K> rejetées (faux négatifs éliminés).

### Patch [gravité] — [sujet]

**Diagnostic** : <raisonnement du Juge>

**Source** : Critique <ID> (angle: <archi|prag|sim>)

**Modification** : <patch_final du Juge — version reformulée si PARTIELLE>
```

Convention préservée : historique de pensée, code applicatif lit "## Patches v1.X" en prioritaire.

### Étape 4.2 — Vérification anti-régression (Python)

```bash
python3 scripts/check_regression.py outputs/<nom_projet>/
```

Le script :
- Parse les sections `## Patches stratégiques vX.Y` de chaque fichier
- Compare la dernière version avec toutes les précédentes
- Alerte si overlap de mots-clés ≥ 50% (sujet re-traité) ou si polarité opposée (contradiction)

Si alerte → présenter à l'user :
> "⚠ Le patch v1.2 sur archi.md touche un sujet déjà patché en v1.1 (polarité opposée). Possible régression. Veux-tu : (a) garder, (b) supprimer le nouveau, (c) consolider en vN.0 ?"

### Étape 4.3 — Générer `sessions_claude_code.md`

Lire `references/handoff-cc.md` (notamment la section "Règle Reset contexte"). Structure de chaque session :

```markdown
### Session N — [titre court]

**Statut** : à faire
**Objectif** : [1 phrase]
**Prérequis** : [sessions à compléter avant]
**Reset contexte** : `nouvelle fenêtre` | `/clear` | `continuer`

**Prompt** :
```
[RÈGLE DE FER COLLÉE]

[Contexte : quoi lire, quoi faire]

Plan d'abord, je valide avant que tu agisses.
```

**Vérifications après** :
- [check 1]
- [check 2]

**Commit attendu** : `[type]: [message court]`

**Mise à jour du plan** : edit sessions_cc.md → `[DONE]` + `Décisions:` + `Divergences:`.
```

**Règles de génération du champ `Reset contexte`** (cf. tableau complet dans `references/handoff-cc.md`) :
- Session 1 → `nouvelle fenêtre` (toujours)
- Session N "lourde" attendue (long prompt, multi-sprints, touche > 4 fichiers) → la suivante prendra `nouvelle fenêtre`
- Session N "légère" enchainée → la suivante prendra `/clear`
- Session N = test pur de ce que Session N-1 a codé → `continuer` (rare)

En-tête du fichier : **règle de fer consolidée** (Phase 1) + table de référence du Reset contexte. (En v3.6, la règle de fer vit surtout dans le `CLAUDE.md` du repo — cf. 4.3bis — donc les prompts de session peuvent être plus légers.)

### Étape 4.3bis — Générer le `CLAUDE.md` du repo cible (v3.6, handoff fichier-resident)

**Toujours**, quel que soit le type. Le plan ne se colle pas dans Claude Code, il **vit dans le repo**. Générer `outputs/<nom_projet>/CLAUDE.md` (destiné à la **racine du repo cible**) à partir du template de `references/handoff-cc.md` (section « Handoff fichier-resident »). Il doit contenir : la **règle de fer** consolidée (Phase 1), les **pointeurs vers les 4 fichiers** du plan, la **discipline harnais** (éval avant features, re-run par session, git checkpoints), et le rappel Reset contexte.

Effet : Claude Code charge `CLAUDE.md` automatiquement à chaque session → contexte persistant, versionné, qui survit aux resets. (Pour un repo multi-outils, générer aussi `AGENTS.md`.) La gate `--handoff=on` (C12) bloque la livraison si ce fichier manque.

### Étape 4.3ter — Générer le `journal.md` du projet (v4.0, suivi vivant)

**Toujours** (utile dès qu'un plan est multi-sessions). Générer `outputs/<nom_projet>/journal.md` selon le schéma `data_model.md §4` : un bloc **« État actuel »** glissant réécrit en tête (phase, sessions faites/N, dernier score Debate Room, prochain pas) + un **Log append-only daté** (une entrée par événement : prévu / réalisé / divergence). Ajouter un **pointeur vers `journal.md`** dans le `CLAUDE.md` (section « Plan — à lire »). C'est la mémoire de suivi qui survit aux resets (context-reset over compaction, cf. `references/harnais.md` §avril 2026) : on rejoue l'état depuis le journal, on ne le résume pas.

### Étape 4.4 — Session CC dédiée à la boucle d'auto-amélioration (si type=skill)

Si type=skill et mémoire ≠ aucune, insérer (Session 2 ou 3) une session dédiée qui câble la **boucle d'auto-amélioration** (cf. `spec_produit.md` §11 + `references/harnais.md`) :
1. Fonction `log_interaction(...)` → `memory/interactions.jsonl`
2. Template `memory/issues.md` + `memory/proposed_fixes.md`
3. Hook au début + fin du main du skill
4. **Runner du golden set** : rejoue les assertions binaires du §10bis et sort un score (la fitness du loop)
5. **Hook `skill-auto-improver`** : lit `issues.md` + golden set → propose un patch → **commit si le score monte / revert sinon** ; `proposed_fixes.md` = audit trail
6. **Déclencheur** : une tâche planifiée (nuit/semaine) qui lance la passe — sans ça, pas de loop
7. **Anti-gaming** : assertions non-gamables, essais isolés (le moteur optimise *contre* le golden set)
8. Test : 2 invocations → 2 lignes dans `interactions.jsonl` ; 1 passe auto-improver à blanc
9. ⚠ Confidentialité : pas de contenus bruts (résumés/métadonnées only)

### Étape 4.5 — Self-diagnosis (Python, plus de LLM)

```bash
python3 scripts/self_diagnosis.py outputs/<nom_projet>/ \
    --type=<app|skill|doc> \
    --memory=<complet|issues_only|aucune> \
    --harness=on \
    --autoimprove=on \
    --handoff=on
```

Le script check (binairement, 0 token) :
- C1 : 3 fichiers obligatoires existent
- C2 : chaque fichier ≥ son seuil de lignes (spec≥80, archi≥60, data≥40, sessions≥30)
- C3 : aucun placeholder résiduel (`[À COMPLÉTER]`, `TBD`, `FIXME`, …)
- C4 : si type=skill et mémoire≠aucune, section "Mémoire du skill" présente
- C5 : sessions_cc.md a une structure de sessions cohérente
- C6 : verdict.json parse et a les clés requises
- C7 : si verdict=patch_required, des sections "## Patches stratégiques vX.Y" existent
- C8 : chaque prompt de session contient "règle de fer"
- C9 (v3.1) : chaque session a un champ `Reset contexte` avec une valeur valide (`nouvelle fenêtre` / `/clear` / `continuer`)
- C10 (v3.3, si `--harness=on`) : `spec_produit.md` a un signal de succès / golden set (H1) ET `archi.md` a une couche harnais (H2/H6). Sans `--harness`, le script tourne à 9 checks (rétro-compatible CI/evals).
- C11 (v3.5, si `--autoimprove=on` ET type=skill) : `spec_produit.md` a une section boucle d'auto-amélioration (§11 : `skill-auto-improver` — signal + mémoire + moteur + déclencheur). Skill-only, off par défaut → evals inchangées.
- C12 (v3.6, si `--handoff=on`) : le dossier du plan contient un `CLAUDE.md` (ou `AGENTS.md`) — le handoff repo-resident généré en 4.3bis. Off par défaut → evals inchangées.

Si `status: FAIL` → ne PAS livrer, reprendre les étapes correspondantes et relancer.

### Étape 4.6 — Livraison

Présenter à l'user :
- Chemin du dossier `outputs/<nom_projet>/`
- Liens `computer://` vers les 4 fichiers + le `CLAUDE.md` du repo (v3.6)
- Résumé 3 lignes : `N critiques évaluées, M confirmées (K rejetées comme faux négatifs), score_convergence X/10, Y sessions générées`
- Handoff (v3.6) : "Copie ce dossier dans ton repo (`CLAUDE.md` à la racine), `git add -A && git commit`, puis ouvre Claude Code dans le repo — il lit `CLAUDE.md` + le plan tout seul. Lance la Session 1." (NE PAS coller le plan comme un prompt jetable.)

---

## Fichiers de référence (chargement à la demande)

| Fichier | Contenu | Quand |
|---------|---------|-------|
| `references/templates/app/*.md` | 4 templates du plan (avec sections harnais en v3.3) | Phase 2.3 |
| `references/harnais.md` | **(v3.3)** Doctrine harnais + checklist H1–H8 + sources | Phase 2.4, 3.1, 4.5 |
| `references/pattern-injection.md` | Chaînage avec pattern-extractor | Phase 2.2 |
| `references/adversarial/critic-architecte.md` | Prompt Architecte | Phase 3.1 |
| `references/adversarial/critic-pragmatiste.md` | Prompt Pragmatiste | Phase 3.1 |
| `references/adversarial/critic-simulateur.md` | Prompt Simulateur | Phase 3.1 |
| `references/adversarial/critic-harnais.md` | **(v3.3)** Prompt Red Team Harnais (H1–H8) | Phase 3.1 |
| `references/adversarial/defenseur.md` | Prompt Défenseur | Phase 3.3 |
| `references/adversarial/juge.md` | Prompt Juge | Phase 3.4 |
| `references/adversarial/observateur.md` | **(v3.2)** Méta-cognitif post-loop | Phase 3.6 |
| `references/adversarial/critic-composite.md` | **Fallback v2** mono-critic | Phase 3.7 si 2+ critics fail |
| `references/workflow.md` | Détail des phases, edge cases | Si confusion |
| `references/handoff-cc.md` | Format détaillé prompt CC | Phase 4.3 |
| `scripts/align_critiques.py` | Merge des 3 critiques | Phase 3.2 |
| `scripts/check_convergence.py` | **(v3.2)** Décide CONTINUE / CONVERGED / etc. | Phase 3.5 |
| `scripts/check_regression.py` | Anti-régression patches | Phase 4.2 |
| `scripts/self_diagnosis.py` | Circuit-breakers Python (9 checks) | Phase 4.5 |
| `scripts/run_evals.py` | **(v3.2)** Runner des golden cases | Hors workflow, en CI |
| `evals/evals.json` | **(v3.2)** Spec des 9 golden cases | Lu par run_evals.py |

---

## Anti-patterns à éviter

- **Spawn séquentiel des 3 critics** au lieu de parallèle → coût ÷ 3 perdu, latence ×3. TOUJOURS un seul message multi-tool-call pour les 3.
- **Skip du Défenseur "parce que les critics sont déjà 3"** → c'est lui qui élimine les faux négatifs. Sans Défenseur, on revient à du v2.0 déguisé.
- **Skip du Juge "parce que le Défenseur a déjà tranché"** → non, le Défenseur défend (avec biais positif), le Juge vérifie en relisant la source.
- **Appliquer les patches REJETÉE** → c'est ajouter du bruit, le Juge a tranché.
- **Ne pas drafter les 4 fichiers en une seule passe.** Drafter 3 + Debate Room + patch + générer le 4e.
- **Ne jamais ré générer le 4e.
- **Ne jamais réécrire un fichier suite à un patch.** Append-only "## Patches stratégiques v1.X".
- **Ne pas zapper l'Étape 1.5 (récap & validation).**
- **MCP tool sans namespace** → "tool not found" silencieux. Format `server_name:tool_name`.
- **Skip de la self-diagnosis Python** → on perd les check binaires gratuits.
- **(v3.2) Désactiver le Refinement Loop "parce que round 1 a un score décent"** → un score de 7 round 1 n'est pas un score de 8. La boucle existe pour faire la dernière mile, c'est précisément là qu'elle a le plus de valeur.
- **(v3.2) Skip de l'Observateur sur un projet complexe** → si la Debate Room a produit ≥ 5 critiques alignées, l'Observateur a du signal à analyser. Ne le skipper QUE sur les projets ultra-simples (1 round CONVERGED direct + ≤ 3 critiques).
- **(v3.2) Lancer `run_evals.py` après chaque modif de prompts d'agent** : faux ami — les evals ne testent QUE les scripts Python. Pour tester les agents, faire un vrai run et faire confiance à l'Observateur + ta lecture humaine.
- **(v3.3) Drafter un plan sans couche harnais** → un plan sans signal de succès (golden set + assertions) est aveugle. Le `critic-harnais` le flague CRITIQUE (H1) et la gate `--harness=on` le bloque (C10). Le harnais n'est pas optionnel dès qu'il y a un golden set.
- **(v3.5) Planifier un skill sans boucle d'auto-amélioration** → un skill sans signal rejouable + mémoire + moteur (`skill-auto-improver`) + déclencheur ne s'améliore jamais sur ses vrais échecs. Le `critic-harnais` (H4b) le flague MAJEUR et la gate `--autoimprove=on` le bloque (C11). NE concerne QUE les livrables de type skill.
- **(v3.5) Confondre « auto-amélioration du livrable » et « auto-amélioration de mode-plan »** → mode-plan ne se réécrit JAMAIS en cours de run (cf. règle de consolidation). L'auto-amélioration de mode-plan lui-même = job de `skill-auto-improver`, séparément, la nuit, nourri par l'Observateur → `_mode-plan-meta/issues.md`.
- **(v3.6) Coller le plan dans Claude Code comme un prompt jetable** → contexte éphémère, perdu au reset. Le plan vit DANS le repo (`CLAUDE.md` à la racine + les 4 fichiers), Claude Code le relit à chaque session. mode-plan génère le `CLAUDE.md` (4.3bis) ; la gate `--handoff=on` (C12) bloque si absent.
- **(v3.3) Garder un fan-out multi-agent sans le passer au test empirique** → si remplacer N agents par 1 appel d'un bon modèle ne baisse pas le score golden, l'orchestration est une taxe. Le `critic-harnais` (H8) doit le challenger. Inverse aussi vrai : ne pas sur-harnacher un projet jetable.

---

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
- Les evals ne testent QUE les scripts Python (déterministes). Les agents LLM (critics, Défenseur, Juge, Observateur) ne sont pas testés automatiquement — leur calibration repose sur l'observation manuelle des premiers runs réels + le feedback de l'Observateur.

### Plan de consolidation v4.0 (anti-bloat)

Si le SKILL.md dépasse 600 lignes OU si le fichier porte ≥ 4 patches en append, faire une réécriture vN.0 manuelle qui intègre les patches dans le body, reset le compteur, préserve l'historique via Git. mode-plan ne s'auto-consolide jamais.

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

---

## Référence d'exemple vivant

Le projet Coach de Sébastien est l'exemple canonique de ce que mode-plan produit. Voir `examples/coach-project/README.md` pour le contexte.
