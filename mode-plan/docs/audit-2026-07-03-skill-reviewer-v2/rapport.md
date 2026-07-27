# Audit skill-reviewer-v2 — mode-plan v4.1 (Mode A)

## Verdict

```
execution_score : 7.1   cadrage_verdict : steelman_tient   tension : false
score_global    : 7.1   (score d'EXÉCUTION A + CODE — jamais pondéré par B)
```

Pas de tension A/B : le cadrage tient (steelman non renversé) ET l'exécution est bonne.
Le résultat central honnête est donc : **le cadrage architectural de mode-plan tient, son
exécution sur 2 outputs réels (plans frontier-kb et skill-reviewer-v2) est bonne, et le
talon d'Achille est dans les scripts-vérifieurs (axe 9 = 6, avec 1 CRITIQUE : le gate
hold-out d'auto_improve est neutralisable en silence par simple suppression du dossier
`_holdout/`)**. Un skill dont la thèse est « la confiance vient des vérifieurs
déterministes » ne peut pas se permettre des vérifieurs qui passent au vert sur des
artefacts absents — c'est le point unique à corriger en priorité absolue.

Aucune lentille dégradée. Aucune instruction cachée détectée. Axes non évaluables : aucun.

## Ce qui tient

Le skill est globalement solide, et plusieurs mécanismes concrets méritent d'être GARDÉS
tels quels :

1. **verify_citations, vérificateur déterministe 0-LLM doublant le Juge**
   (`scripts/verify_citations.py`) : le maillon faible connu des architectures à juge est
   le seul agent doublé d'un check qui rétrograde ses verdicts non ancrés. C'est le bon
   pattern — son seul défaut est le fail-open (cf. Axe 9), pas son existence.
2. **Le Défenseur anti-patchwork** (`references/adversarial/defenseur.md#S002`) : répond à
   un mode d'échec mesuré (patcher des sujets déjà traités = bruit append-only) et produit
   une entrée par critique reçue, même PAS_TROUVÉ. Il a joué son rôle dans cet audit même
   (5 findings nuancés en PARTIEL, 1 TROUVÉ).
3. **self_diagnosis multi-gates C1–C14** (`SKILL.md#S036`) : couche de vérification
   déterministe post-génération, extensible par flags — le principe est le bon, seule
   l'activation opt-in silencieuse est à durcir (A-009, nuancé par le Défenseur).
4. Le fan-out n'est pas un article de foi : il a survécu à une **ablation empirique datée
   (H8, 3 agents hérités supprimés)**, et le produit livré (handoff fichier-résident +
   harnais dans le plan) transforme la faillibilité résiduelle du plan en détection bon
   marché à l'implémentation — validé par les faits : 4 sessions, divergences mineures.

## Lentille A — exécution (axes 1–8, 10)

**Axe 2 (8) — RAS.** Solide, rien à signaler au-delà du score.
**Axe 7 (8) — RAS.** Solide, rien à signaler au-delà du score.
**Axe 10 (8) — RAS.** Solide, rien à signaler au-delà du score.

### Axe 1 — fidélité au contrat sur outputs réels : 7

- **A-001 [IMPORTANT, exécuté, Défenseur : PARTIEL/MODÉRÉE]** — Le plan frontier-kb a été
  livré après le round 1 seul alors que le verdict enregistré est `major_revision`
  (journal : 19 confirmées, score 4,45) : ni round 2, ni bannière ⚠ dans les fichiers
  livrés (`SKILL.md#S025`). Nuance du Défenseur : le SKILL.md prévoit bien, sur
  major_revision, d'avertir l'user et de lui demander s'il continue — la déviation est
  donc possiblement un choix utilisateur non tracé, mais précisément : rien dans les
  livrables n'en garde la trace, ce qui reste le problème.
- **A-002 [IMPORTANT, exécuté]** — Les statistiques affirmées dans les deux livrables
  (« 19 confirmées, score 4,45 », « 22 patchs foldés ») sont invérifiables ex post : aucun
  dossier `.mode-plan/` (critiques, défenses, verdicts, citations_report) n'accompagne les
  dossiers livrés, contredisant la promesse d'observabilité (`SKILL.md#S020`).
- A-003 [MINEUR, PARTIEL] : incohérences résiduelles frontier-kb dues à l'append-only
  (périmètre V1-core G8, supersession G3) — convention « patches prioritaires » assumée,
  mais un exécuteur qui lit le corps seul peut câbler le mauvais périmètre.

**Cause transverse (A-001 + A-004 + A-011)** : vu des deux bouts de la chaîne, la cause
commune est que plusieurs garde-fous de mode-plan sont **déclaratifs sans mécanisme
d'application** — la boucle de convergence, le format append-only et le timeout critic
reposent sur la discipline de l'orchestrateur LLM, sans gate déterministe qui vérifie la
conformité de l'output livré. C'est le plafond P-003.

### Axe 3 — garde-fous et sécurité d'entrée : 7

- A-008 [MINEUR] : le mode iterate_existing ingère des plans externes sans bornes « donnée
  non fiable » ni consigne anti-injection dans les prompts adversariaux (`SKILL.md#S018`) —
  alors que le plan produit pour skill-reviewer-v2 impose précisément ce mécanisme. Risque
  faible en mono-utilisateur local, mais écart notable avec sa propre doctrine.
- A-009 [MINEUR, Défenseur : TROUVÉ/MODÉRÉE — conservé nuancé] : gates C10–C14 opt-in ;
  un flag omis = check sauté sans trace. Nuance forte : la commande canonique documentée
  dans le SKILL.md passe déjà tous les flags explicitement — le risque réel est limité à
  un orchestrateur qui dévie du template. Se rattache à la cause fail-open (cf. Axe 9).

### Axe 4 — context engineering : 7

- A-010 [MINEUR, PARTIEL] : SKILL.md à 501 lignes (~9 700 tokens) au-dessus de la cible
  <500/<5 000, pourtant marqué « ✅ RÉSOLU (v4.1) » dans `_mode-plan-meta/issues.md#S005`.
  La progressive disclosure est par ailleurs réelle (références à la demande) : impact
  modéré, mais le statut « résolu » est factuellement faux.

### Axe 5 — chemins dégradés : 7

- A-011 [MINEUR] : le fallback « critic sans réponse après ~3 min → continuer avec les 2
  autres » (`SKILL.md#S027`) n'a aucun mécanisme d'application — l'orchestrateur n'a pas
  de timer sur les spawns. Les autres chemins dégradés (JSON malformé, fallback composite,
  verdict illisible) sont eux bien câblés. Cf. cause transverse P-003 (et la coquille
  « 2 autres » pour 4 critics rejoint A-005).

### Axe 6 — cohérence des contrats inter-agents : 6 (axe le plus faible avec le 9)

- **A-005 [IMPORTANT, PARTIEL/MODÉRÉE]** — Dérive 3-vs-4 critics non résorbée depuis
  v3.3 : « Merge des 3 critiques », « un seul message multi-tool-call pour les 3 »,
  « continuer avec les 2 autres », enum d'IDs/angles du Défenseur excluant HARN-xxx alors
  que les runs réels en produisent (`references/adversarial/defenseur.md#S002`). Chaque
  sous-agent reçoit un schéma d'entrée partiellement faux. Nuance : la règle « une entrée
  par critique reçue » a permis aux runs réels de tolérer la dérive — mais la tolérance
  observée n'est pas un contrat.
- **A-007 [IMPORTANT, PARTIEL/MODÉRÉE]** — Table de décision verdict_global du Juge non
  exclusive (`references/adversarial/juge.md#S002`) : un score 9 / 0 CRITIQUE satisfait
  « go » ET « patch_required » ; un score 4 / 1 CRITIQUE satisfait « patch_required » ET
  « major_revision ». Nuance : check_convergence.py retranche une décision déterministe
  en aval — mais le verdict textuel du Juge, lui, reste non déterministe et c'est lui que
  lit l'orchestrateur en premier.
- **A-004 [IMPORTANT, exécuté]** — L'output réel skill-reviewer-v2 dévie du contrat de
  Phase 4 : fichiers « v2 CONSOLIDÉE » (réécriture) au lieu de patches append-only, aucun
  bloc au template Diagnostic/Source/Modification (`SKILL.md#S030`) ; la gate C7 se
  contente de l'existence d'une section Patches. → rejoint la cause transverse P-003.
- A-006 [MINEUR] : puce cassée ligne 481 (« **Ne jamais ré générer le 4e. ») et coquille
  « tu trancles » dans le prompt du Juge — zones lues par des sous-agents.

### Axe 8 — déclenchement et description : 7

- A-012 [MINEUR] : description par ailleurs exemplaire (998 car., périmètre négatif,
  désambiguïsation pipeline-plafonds), mais « fais-moi un plan, on planifie d'abord, avant
  de coder » collisionne avec superpowers:writing-plans et superpowers:brainstorming dans
  le même environnement — routage non arbitré (`SKILL.md#S001`).

## Audit du code (Axe 9) : 6 — tag : statique / non exécuté

### Cause racine transverse unique — « vérifieur fail-open : artefact manquant/vide = succès »

Cinq findings code sont la MÊME cause racine et sont fusionnés ici (dédup anti-patchwork) :
un vérifieur qui, face à un artefact absent, vide ou au schéma dérivé, retourne le
meilleur score possible au lieu d'échouer. Vu des deux lentilles (CODE sur les scripts,
A sur les flags opt-in A-009), la cause commune est **une politique par défaut fail-open
là où la fonction même de ces scripts exige du fail-closed**.

| Script | Symptôme | Gravité |
|---|---|---|
| `scripts/auto_improve.py` (**CODE-001**) | `_score_capability(HOLDOUT_DIR) if HOLDOUT_DIR.is_dir() else 1.0` : dossier hold-out supprimé/renommé (y c. par un patch LLM via --sandbox-apply) → gate anti-gaming validé à 1.0 sans rien mesurer, dans le vérifieur qui décide COMMIT/REVERT | **CRITIQUE** |
| `scripts/check_regression.py` (CODE-003) | fichiers requis absents → `[]` → PASS/exit 0 ; « 0 régression » indistinct de « 0 fichier analysé » | IMPORTANT |
| `scripts/run_evals.py` (CODE-004) | `cases = spec.get("cases", [])` → « 0/0 passed », exit 0 en CI directe | IMPORTANT |
| `scripts/check_convergence.py` (CODE-005) | bloc `statistiques` absent → score=0, confirmed=0 → NO_ISSUES → « deliver » à tort (Défenseur PARTIEL/FAIBLE : le mode safe documenté couvre le JSON malformé, pas le JSON valide-mais-vide) | IMPORTANT |
| `scripts/verify_citations.py` (CODE-006) | 0 citation collectée → `taux_ancrage=1.0`, exit 0 : score parfait sur artefacts manquants | IMPORTANT |

**Correctif unique** (une politique, cinq applications) : artefact requis manquant ou
vide = échec explicite ou statut dédié (HOLDOUT_MISSING, NO_CASES, NO_CITATIONS,
STATS_MISSING, MISSING_FILES), jamais un PASS ni un 1.0. Jamais deux items pour la même
cause : c'est UNE reco (R1).

### Autres findings code

- **CODE-002 [IMPORTANT, PARTIEL/MODÉRÉE]** — `subprocess.run(apply_cmd, shell=True)`
  (bandit B602 HIGH/HIGH, `scripts/auto_improve.py`) sur une commande issue de
  skill-auto-improver, donc d'une sortie LLM requalifiée « ENTRÉE DE CONFIANCE » par le
  docstring. Nuance : le risque est documenté et assumé dans le code — mais documenter
  n'est pas fermer ; passer en argv sans shell ou exiger une confirmation humaine.
- CODE-007 [MINEUR] : parseur JSON « tolérant » dupliqué à l'identique dans 5 fichiers
  (contre la règle « une seule source » du repo) ; rattrapage premier-{/dernier-} peut
  parser le mauvais objet. À factoriser dans `_parse.py`.
- CODE-008 [MINEUR, PARTIEL] : `--dry-run` no-op trompeur (`store_true` + `default=True`) ;
  nuance : le docstring documente le défaut, mais le --help ment. Retirer ou constifier.

## Lentille B — cadrage

**Steelman (d'abord)** : le design actuel est le meilleur argument pour lui-même — un
skill qui applique à sa propre architecture la discipline qu'il exige des plans qu'il
produit. Fan-out survivant à une ablation datée (H8), ensemble de vérifieurs rejeté sur
mesure et best-of-N adopté sur mesure, Juge doublé d'un vérificateur déterministe 0-LLM,
Défenseur répondant à un mode d'échec mesuré, débat réservé aux décisions à fort enjeu
(F-026), sorties NO_ISSUES/PLATEAU (F-022), handoff fichier-résident qui transforme la
faillibilité résiduelle en détection bon marché à l'implémentation (4 sessions,
divergences mineures). « Renverser ce design exigerait un mécanisme que sa propre
machinerie de falsification n'aurait pas pu tester ; je n'en ai pas trouvé. »

**Verdict : steelman_tient.** Aucun reframe dominant, aucun mécanisme d'archi ne
verrouille un plafond de cadrage.

**Plafond résiduel sondé (non dominant)** : la Debate Room critique le TEXTE du plan,
jamais sa correspondance au monde — score_convergence = accord entre agents LLM, pas
faisabilité réelle ; les 3 divergences réelles observées (script sans WebSearch, prémisse
d'un cas golden cassée, check trop grossier) sont toutes des échecs de
correspondance-au-réel invisibles au débat rhétorique. Neutralisé par le mandat 1 : (a) le
harnais que le plan installe absorbe ces résidus à coût mineur ; (b) « ne code rien »
n'interdit pas les checks déterministes — un lint de faisabilité s'ajoute SANS changer
l'architecture ; (c) améliorer le critic-simulateur est de l'exécution, pas un reframe.
Classe : contournable-ingénierie → P-002.

## Plafonds (Axe 11)

| ID | Plafond | Classe | Contournement | Handoff |
|---|---|---|---|---|
| P-001 | Vérifieurs fail-open : artefact manquant/vide = succès, jusque dans le gate COMMIT/REVERT (evidence : `scripts/auto_improve.py`, `else 1.0`) | contournable-ingénierie | Politique fail-closed uniforme + 1 test d'absence d'artefact par vérifieur (supprimer l'artefact, exiger l'échec) | manuel |
| P-002 | La Debate Room évalue le texte, pas la correspondance au monde (evidence : `SKILL.md#S025`, boucle pilotée par score_convergence inter-LLM) | contournable-ingénierie | Lint de faisabilité déterministe (capacités outillage, prémisses des golden cases) + renforcer le critic-simulateur ; le harnais d'implémentation reste le filet | skill-creator-v12 |
| P-003 | Garde-fous déclaratifs sans mécanisme d'application : boucle de convergence, append-only, timeout critic reposent sur la discipline de l'orchestrateur LLM (evidence : `SKILL.md#S030`, template patch non appliqué dans l'output réel) | contournable-ingénierie | Gates déterministes sur les LIVRABLES : bannière ⚠ exigée si major_revision sans round 2, format patch vérifié par regex (pas seulement l'existence de la section), `.mode-plan/` livré obligatoire | skill-creator-v12 |

Aucun plafond structurel-IA-seule : chaque faiblesse a un contournement déterministe
(script, gate, lint) — pas de handoff labo-recherche nécessaire. Anti-marteau-clou :
aucune reco n'ajoute d'agent ; tout se règle par vérifieurs déterministes et prompts plus
contraignants.

## Plan d'amélioration (priorisé)

| # | Reco | Findings | Effort | Handoff |
|---|---|---|---|---|
| R1 | Politique fail-closed sur les 5 vérifieurs + statuts dédiés (HOLDOUT_MISSING en tête — c'est le gate COMMIT/REVERT) et trace quand un gate C10–C14 est sauté | CODE-001, 003, 004, 005, 006, A-009 | quick-win | manuel |
| R2 | Supprimer `shell=True` (argv liste) ou confirmation humaine de `apply_cmd` | CODE-002 | quick-win | manuel |
| R3 | Gate de livraison : bloquer si verdict=major_revision sans round 2 ni bannière ⚠, et exiger `.mode-plan/` dans les livrables | A-001, A-002 | <1j | skill-creator-v12 |
| R4 | Résorber la dérive 3-vs-4 (une passe globale : merge, anti-patterns, enums Défenseur/Juge), rendre la table verdict_global exclusive (if/elif ordonné), vérifier le format patch par regex dans C7 | A-005, A-007, A-004, A-006 | <1j | skill-creator-v12 |
| R5 | Lint de faisabilité déterministe (P-002) : vérifier capacités outillées des scripts planifiés et prémisses des golden cases avant livraison | B (plafond résiduel) | >1j | skill-creator-v12 |
| R6 | Bornes « donnée non fiable » + consigne anti-injection sur les plans externes en iterate_existing | A-008 | quick-win | skill-creator-v12 |

R1 avant tout : tant que les vérifieurs peuvent passer au vert sur du vide, toutes les
autres garanties du skill (auto-amélioration gated, convergence, ancrage des citations)
sont conditionnelles.

## Annexes

**Écartés par le Défenseur (TROUVÉ force FORTE)** : aucun. (A-009, TROUVÉ force MODÉRÉE,
est conservé nuancé dans l'Axe 3 conformément au contrat.)

**Findings mineurs hors top 20 (1 ligne)** :
- CODE-009 [MINEUR] l3_gate : l'argument `--l3 on/off` est parsé mais jamais lu.
- CODE-010 [MINEUR] best_of_n : rubrique de scoring par présence de mots-clés (fragile).
- CODE-011 [MINEUR] align_critiques : le score global pondéré remplace silencieusement par le neutre.
- B-002 [MINEUR] Signal de succès de mode-plan sur lui-même (self_eval_debate sur plans-graine) partiellement auto-référent.
- B-003 [MINEUR] Les 4 critics + Défenseur + Juge lisent tous le même input (brief consolidé) — diversité d'entrée limitée.
