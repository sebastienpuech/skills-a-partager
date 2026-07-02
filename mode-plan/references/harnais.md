# Harnais — doctrine (v3.4, Harnais-Aware)

> Chargé en **Phase 2.3bis** (le draft doit contenir les sections harnais), en **Phase 3.1** (le `critic-harnais` s'en sert de grille), et en **Phase 4.5** (la self-diagnosis `--harness=on` vérifie la présence des sections).
> Source : état de l'art harnais 2025-2026 (Anthropic Engineering, Chroma, débat Cognition/Anthropic, littérature RLVR / LLM-as-judge). Voir bloc Sources en bas.

---

## Principe directeur

Avec un modèle frontière, **l'intelligence n'est plus le goulot — le harnais l'est.** La plupart des échecs d'agent ne sont pas des échecs de raisonnement mais des échecs de harnais : mauvais retour d'outil, contexte pollué, aucun signal de réussite, pas de reprise après une erreur, pas d'éval pour attraper la régression.

Conséquence pour un plan mode-plan : on cesse de planifier *comment l'agent pense* (l'orchestration cognitive, que le modèle absorbe génération après génération) pour planifier **ce que l'agent voit, peut faire, et peut vérifier**. Le plan doit décrire un environnement et une boucle de feedback, pas seulement une suite de features.

**Règle de tranchage de l'orchestration (anti-bloat cognitif)** : pour tout fan-out d'agents (Tournament, panel, multi-critics), poser le test empirique — *si on remplace les N agents par 1 seul appel d'un bon modèle, est-ce que le score golden baisse ?* S'il ne baisse pas, l'orchestration substituait une capacité que le modèle a maintenant → **la supprimer**. S'il baisse, elle injecte de l'information/vérification réelle → la garder. La vraie parallélisation (un agent par contenu distinct) reste valable ; la redondance cognitive est une taxe.

**Limites du domaine vs limites génériques (v4.1)** : le harnais gère les échecs GÉNÉRIQUES du modèle (H1–H8). Les échecs SPÉCIFIQUES au domaine du skill (ce que le modèle ne sait pas faire *pour cette tâche*) doivent être nommés séparément (**H9**) — sinon on scaffolde à l'aveugle. Nommer → classer → contourner → prouver (par un cas golden). Alimenté par `diagnostic-plafonds`.

**Règle du writer unique (orchestration 2026)** : les **lectures / l'intelligence parallélisent** (un agent par contenu distinct, exploration en éventail) ; les **écritures / décisions de synthèse restent single-threaded** — un seul agent consolide et tranche, en une passe unifiée. Des sous-agents qui écrivent en parallèle prennent des décisions implicites contradictoires. C'est la résolution du débat Cognition/Anthropic : pas « multi-agent oui/non » mais « parallélise les lectures, sérialise les écritures ». *(mode-plan applique déjà ça : critics en parallèle, Juge/patch en série — c'est une formalisation, pas un changement.)*

---

## Les 6 couches du harnais

Chaque couche liste : le **principe**, ce que **le plan doit contenir**, et où ça atterrit dans les 4 fichiers.

### 1. Context engineering (le socle)

Le contexte est une ressource finie à rendement décroissant (**context rot** : la fiabilité chute, de façon non uniforme, à mesure que l'input grossit — mesuré sur 18 modèles par Chroma). Objectif : *le plus petit ensemble de tokens à haut signal qui maximise la probabilité du résultat voulu.*

Le plan doit contenir :
- **System prompt à la « bonne altitude »** : ni logique if-else hardcodée et fragile, ni vague. (→ `archi.md` §4bis ; pour un skill, la structure du SKILL.md)
- **Stratégie de récupération just-in-time** : garder des identifiants légers (chemins, requêtes, liens) et charger à l'exécution plutôt que tout pré-charger. (→ `archi.md`)
- **Plan de gestion du contexte long-horizon** : compaction → note-taking structuré → sous-agents, dans cet ordre. Quel budget de contexte par étape, quoi garder vs résumer. (→ `archi.md` §4bis)

### 2. Outils (le contrat agent ↔ monde)

Le mode d'échec le plus courant est le **jeu d'outils boursouflé**. Règle : *si un ingénieur humain ne sait pas dire quel outil utiliser dans une situation, l'agent ne le saura pas non plus.*

Le plan doit contenir :
- Un set d'outils **minimal et non-redondant**, chaque outil au périmètre net. (→ `archi.md` §2 et §4bis)
- Des **retours d'outils token-efficients et des erreurs actionnables** (le modèle doit pouvoir se corriger seul à partir du message d'erreur). (→ `archi.md` §4bis)
- Pour un skill : des **exemples canoniques** (few-shot) plutôt qu'une laundry-list d'edge cases. (→ `spec_produit.md` golden set)
- **Token-efficience des outils (état 2026)** : dès que le plan expose >5 outils ou un MCP volumineux, prévoir le **chargement différé** des définitions d'outils (l'agent ne voit que les outils pertinents, pas tout le catalogue) et, pour les enchaînements, l'**exécution par code** plutôt que N appels d'outils séquentiels (le modèle écrit du code qui appelle les outils et ne renvoie que le résultat filtré dans le contexte — gains de tokens d'un ordre de grandeur). Ajouter des **exemples d'usage** par outil ambigu. (→ `archi.md` §4bis)

### 3. Vérification & évals (la colonne vertébrale)

C'est la couche la plus rentable et le cœur de la recherche actuelle. Un **vérifieur fiable et pas cher permet d'utiliser un générateur plus simple.**

Le plan doit contenir :
- Un **golden set tenu à l'écart + assertions binaires** (vrai/faux, vérifiables sans LLM quand c'est possible — esprit **RLVR** : ne valider que ce qui passe un check programmatique). Rejoué à **chaque** changement. Distinguer deux suites : *capability* (pass-rate bas = la colline à gravir) et *regression* (~100 % = le garde-fou) ; un cas capability saturé gradue en regression. Grader l'**état final**, pas le chemin d'étapes. (→ `spec_produit.md` §10bis, `sessions_claude_code.md` session harnais)
- Un **vérifieur explicite** quand la sortie n'est pas trivialement checkable (esprit *agentic reward modeling* : combiner jugement et signaux de correction vérifiables — factualité, contraintes). (→ `archi.md` §4bis)
- **Prudence sur le LLM-as-judge** : utile mais à ancrer sur du réel. Les **utilisateurs simulés par LLM sont des proxies non fiables** pour évaluer un agent (*Lost in Simulation*). Donc un golden set ancré sur des cas réels > un juge LLM seul. (→ `spec_produit.md`)
- **Anti-gaming (le revers du RLVR)** : dès qu'on optimise contre une cible vérifiable, on invite le **reward-hacking** — l'agent satisfait la lettre de l'assertion sans l'esprit. Anthropic (2025) montre qu'apprendre à hacker des tests *généralise* vers sabotage/tromperie (misalignment 34–70 %), réductible par *inoculation prompting*. Le plan doit donc : (a) des **graders résistants au bypass** (pas un check qu'on satisfait trivialement) ; (b) **un essai = un environnement propre** (pas d'accès à l'historique des essais ni aux réponses attendues) ; (c) si auto-amélioration : surveiller la généralisation hors-distribution, pas seulement le score golden. (→ `spec_produit.md` §10bis, `archi.md` §4bis)

### 4. Mémoire & état (franchir les fenêtres de contexte)

Un agent long-horizon travaille en sessions discrètes, chacune sans mémoire de la précédente. Le harnais bridge le trou.

Le plan doit contenir :
- **Note-taking structuré / progress file** persistant hors contexte (ex. `claude-progress.txt`, `NOTES.md`, journal append-only). (→ `archi.md` §4bis ; pour un skill : section « Mémoire du skill »)
- **Checkpoints git + état propre en fin de session** (commits descriptifs, possibilité de revert vers un état sain). (→ `sessions_claude_code.md`, déjà couvert par le Protocole anti-régression — le rendre explicite comme harnais)
- Pour les très longues tâches : **split initializer / worker** — une première session qui pose l'environnement (feature list, `init.sh`, repo), puis des sessions incrémentales (une feature à la fois, jamais one-shot). (→ `sessions_claude_code.md`)

### 5. Observabilité (voir *pourquoi* ça échoue)

Sans traces, un échec d'agent est un échec opaque.

Le plan doit contenir :
- **Logs/traces structurés** des décisions et appels d'outils, pas seulement du résultat final. (→ `archi.md` §8 Observabilité, à enrichir)
- Un moyen de **rejouer / inspecter** un run raté (artefacts intermédiaires conservés — comme le fait déjà mode-plan avec `.mode-plan/*.json`). Corollaire de méthode : **on ne fait pas confiance à un score d'éval tant qu'on n'a pas lu des traces réelles** (error-analysis sur un échantillon de runs ratés > moyenne agrégée). (→ `archi.md` §8)

### 6. Garde-fous (le runtime déterministe)

Le harnais valide, autorise, exécute et loggue chaque action proposée par le modèle. Séparation des responsabilités : **le modèle propose, le harnais dispose.**

Le plan doit contenir :
- **Budgets** (tokens / steps / temps), **timeouts**, **caps d'itérations**, **circuit-breakers**. (→ `archi.md` §4bis et §4 garde-fous)
- **Human-in-the-loop** sur les actions sensibles ; **sandbox** pour l'exécution. (→ `archi.md` §7)
- Si l'agent ingère du contenu non fiable (web, fichiers tiers) : **design anti prompt-injection** (isoler données non fiables du flux de contrôle). (→ `archi.md` §7)

---

## Boucle d'auto-amélioration (cas skill) — l'union des couches 3 et 4

Un skill livré n'est pas fini : il doit pouvoir s'améliorer sur ses *vrais* échecs après livraison. C'est la couche 3 (signal de succès) branchée sur la couche 4 (mémoire) via un moteur qui patche et mesure. Pour un plan de type **skill**, le plan doit prévoir les 5 pièces :

1. **Signal rejouable** : le golden set + assertions binaires (H1) — la fonction de fitness du loop.
2. **Mémoire d'exécution** : `interactions.jsonl` (log) + `issues.md` (échecs réels) + `proposed_fixes.md` (audit trail).
3. **Moteur** : `skill-auto-improver` — lit issues + golden set, propose un patch, **commit si le score monte / revert sinon**.
4. **Déclencheur** : une tâche planifiée (nuit/semaine) qui lance la passe — sinon le loop n'existe que sur le papier.
5. **Garde-fou anti-gaming** : le moteur optimise *contre* le golden set → c'est exactement le reward-hacking. Assertions résistantes au bypass, essais isolés (cf. anti-gaming, couche 3).

Sans déclencheur ni mémoire, ce n'est pas un loop — juste un test ponctuel. Sans anti-gaming, le loop apprend à tricher son propre golden set. (→ `spec_produit.md` §11, `sessions_claude_code.md` session auto-amélioration)

---

## Checklist Harnais (ce que le `critic-harnais` exige et ce que la gate vérifie)

Un plan est « harnais-complet » s'il répond OUI à chacune :

- [ ] **H1 — Signal de succès** : existe-t-il un golden set + des assertions (idéalement binaires) qui disent si une sortie est bonne, rejouables à chaque changement ? (`spec_produit.md`)
- [ ] **H2 — Vérification (fiable ET non-gamable)** : la couche qui vérifie est-elle distincte de celle qui génère ? Vérifieur cheap quand la sortie n'est pas trivialement checkable ? Et surtout : le grader est-il **résistant au gaming** (essai isolé, pas de fuite des réponses attendues) ? Un signal de succès qu'on peut satisfaire sans faire le travail est pire que pas de signal. (`archi.md`, `spec_produit.md`)
- [ ] **H3 — Contexte** : y a-t-il une stratégie explicite de budget de contexte (JIT, compaction, note-taking) plutôt que « tout charger » ? (`archi.md`)
- [ ] **H4 — Mémoire/état** : comment l'état survit-il entre sessions/fenêtres ? Checkpoints + reprise après erreur ? (`archi.md` + `sessions_claude_code.md`)
- [ ] **H4b — Auto-amélioration (si type=skill)** : le plan prévoit-il la boucle — signal rejouable + mémoire (interactions/issues/proposed_fixes) + moteur `skill-auto-improver` (commit/revert) + déclencheur planifié + garde-fou anti-gaming ? Absente pour un skill → **MAJEUR**. (`spec_produit.md` §11)
- [ ] **H5 — Observabilité** : peut-on savoir *pourquoi* un run a échoué (traces/artefacts), pas seulement *qu'il* a échoué ? (`archi.md`)
- [ ] **H6 — Garde-fous** : budgets, timeouts, caps, HITL/sandbox sont-ils définis ? (`archi.md`)
- [ ] **H7 — Outils** : set minimal, non-redondant, erreurs actionnables ? Chargement différé / exécution par code si gros jeu d'outils ? (`archi.md`)
- [ ] **H8 — Justification du fan-out** : chaque multi-agent passe-t-il le test empirique (vs 1 appel fort) ? Les écritures sont-elles single-threaded ? Sinon, le simplifier. (`archi.md` §4)
- [ ] **H9 — Limites LLM spécifiques au domaine** : le plan nomme-t-il ce que le modèle ne sait PAS faire de façon fiable *pour cette tâche précise* (au-delà des limites génériques H1–H8), chaque limite **classée** (contournable-ingénierie / structurel-IA-seule / irréductible), **contournée**, et **prouvée par un cas golden** ? Alimenté par `diagnostic-plafonds`. Absent pour un skill/agent non trivial → **MAJEUR**. (`spec_produit.md` §12bis)

Gravité par défaut si manquant : **H1, H2 = CRITIQUE** (sans signal de succès ni vérification — ou avec une vérification gamable —, le reste est aveugle). **H3, H4 = MAJEUR**. **H5, H6, H7, H8 = MAJEUR ou MINEUR** selon l'enjeu du projet.

---

## Ancrage dans l'écosystème de Sébastien

Plusieurs briques harnais existent déjà — l'enjeu est de les rendre systématiques dans tout plan, pas périphériques :

- **`skill-auto-improver`** (assertions binaires + commit si le score monte / revert sinon) = boucle de vérification type RLVR + checkpoints. → couche 3 + 4.
- **`projet-vivant`** (journal append-only + bloc « État actuel » glissant) = note-taking structuré / mémoire. → couche 4.
- **Golden sets + `run_evals.py`** de mode-plan lui-même = évals. → couche 3.
- **`orchestration-patterns`** (circuit-breakers, auto-diagnostic, caps) = garde-fous. → couche 6.
- **CLAUDE.md du vault** (« les règles critiques vont dans CLAUDE.md ») = règles qui survivent à la compaction. → couche 1.

Un plan mode-plan doit donc, quand c'est pertinent, **réutiliser ces briques** plutôt que réinventer.

---

## Sources

- Anthropic — *Effective context engineering for AI agents* (sept. 2025) : https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic — *Effective harnesses for long-running agents* (nov. 2025) : https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic — *Writing tools for AI agents* : https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic — *Demystifying evals for AI agents* (jan. 2026) — split capability/regression, grade-the-output : https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Anthropic — *Code execution with MCP* (nov. 2025) — exécution par code, -98,7 % tokens : https://www.anthropic.com/engineering/code-execution-with-mcp
- Anthropic — *Advanced tool use* (nov. 2025) — Tool Search Tool (defer_loading), Programmatic Tool Calling : https://www.anthropic.com/engineering/advanced-tool-use
- Anthropic — *Emergent misalignment from reward hacking* (nov. 2025) — anti-gaming, inoculation prompting : https://www.anthropic.com/research/emergent-misalignment-reward-hacking
- Chroma — *Context Rot: How Increasing Input Tokens Impacts LLM Performance* : https://www.trychroma.com/research/context-rot
- Débat *Don't Build Multi-Agents* (Cognition) vs *multi-agent research system* (Anthropic) — « la tâche choisit l'architecture » : https://news.smol.ai/issues/25-06-13-cognition-vs-anthropic
- Cognition — *Multi-agents that work* (avr. 2026) — règle du writer unique (writes single-threaded) : https://cognition.ai/blog/multi-agents-working
- *Agentic Reward Modeling* (arXiv 2502.19328) ; *From Generation to Judgment: LLM-as-a-judge* (arXiv 2411.16594) ; *Lost in Simulation* (arXiv 2601.17087) ; *Holistic Agent Leaderboard* (arXiv 2510.11977) ; *Terminal-Bench* (arXiv 2601.11868).

---

## Ajout avril 2026 (v4.0) — harnais 3-agents & context-resets

> Append (mode-plan v4.0, Session 5). Ne réécrit rien au-dessus ; met la doctrine à la frontière la plus récente.

### Le harnais 3-agents Planner / Generator / Evaluator

L'état de l'art (avr. 2026) converge sur une **séparation des rôles en trois** à l'intérieur d'une boucle, plutôt qu'un fan-out large et indifférencié :

- **Planner** — décompose la tâche, fixe le *signal de succès* (les assertions à satisfaire) AVANT toute génération. Il ne génère pas la solution ; il définit à quoi ressemble « réussi ».
- **Generator** — produit la solution candidate contre ce signal. Un seul writer (règle du writer unique) ; peut explorer plusieurs pistes en lecture mais consolide en série.
- **Evaluator** — vérifie la sortie contre les assertions du Planner (grade-the-output, non-gamable), lit les traces des échecs (error-analysis, H5), et renvoie un feedback actionnable au Generator.

Le gain vient de la **frontière nette** entre « définir le succès », « produire », et « juger » — pas du nombre d'agents. Un Evaluator qui partage le contexte du Generator hérite de ses angles morts ; il doit juger sur le signal, pas sur la rhétorique. *(mode-plan v4.0 instancie déjà ce triptyque : la Debate Room = Planner+Generator implicites, `self_eval_debate.py` + `verify_citations.py` + `_meta_eval.py` = Evaluator vérifié.)*

### Context-resets over compaction

Sur une tâche longue, deux stratégies s'opposent pour tenir dans la fenêtre :
- **Compaction** — résumer l'historique pour le comprimer. Risque : le résumé perd du signal de façon non uniforme (context rot déplacé, pas résolu) et fige des erreurs dans le résumé.
- **Context-reset** (recommandé avr. 2026) — repartir d'un contexte **propre** en ne re-chargeant que des **artefacts durables et vérifiables** (fichiers du plan, `.mode-plan/*.json`, journal, golden set) via récupération just-in-time. L'état vit sur le disque (mémoire externe), pas dans l'historique de conversation.

Conséquence pour un plan : préférer une **mémoire fichier-résidente rejouable** (ce que fait `_mode-plan-meta/` + `journal.md` + les `recorded/`) à un long historique compacté. Un run raté se **rejoue** depuis les artefacts, il ne se **résume** pas. C'est la même logique que le handoff fichier-résident (`CLAUDE.md`) : le contexte survit aux resets parce qu'il est sur le disque, versionné.

### Sources (avril 2026)
- Anthropic — *Effective context engineering for AI agents* (context-resets over compaction, just-in-time retrieval).
- Cognition — *Multi-agents that work* (avr. 2026) — writer unique + rôles Planner/Generator/Evaluator.
- Chroma — *Context Rot* (la compaction déplace le problème, ne le résout pas).
