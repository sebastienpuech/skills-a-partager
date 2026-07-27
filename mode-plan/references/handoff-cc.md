# Handoff vers Claude Code — format détaillé des prompts de session

> Référence pour Phase 4 : comment formater chaque session dans `sessions_claude_code.md`
> pour qu'un copy-paste dans CC exécute la session sans question résiduelle.

---

## Handoff fichier-resident (v3.6) — le plan vit dans le repo, on ne le colle pas

**Principe (couche mémoire du harnais)** : ne PAS coller le plan comme un prompt jetable. Le plan **vit dans le repo cible** et Claude Code le **relit** à chaque session — contexte persistant, versionné, qui survit aux resets et à la compaction. C'est la différence entre un agent qui réapprend à chaque fois et un agent qui a une mémoire.

Concrètement, mode-plan génère en **Phase 4.3bis** un **`CLAUDE.md`** (racine du repo cible) qui : consolide la **règle de fer** (immuable, chargée à chaque session), **pointe vers les 4 fichiers** du plan (source de vérité), et rappelle la **discipline harnais** (éval avant features, re-run par session, git checkpoints).

Le handoff devient : « copie le dossier du plan dans ton repo, commit, `cd` + ouvre Claude Code — il charge `CLAUDE.md` tout seul ». Les prompts de session ci-dessous deviennent alors **plus légers** (ils référencent les fichiers au lieu de ré-embarquer la règle de fer) — le format self-contained reste valable en *fallback* (outil sans CLAUDE.md, ou prompt isolé).

> Portabilité : pour un repo multi-outils, générer aussi (ou à la place) un **`AGENTS.md`** (standard ouvert) au même contenu. Claude Code lit `CLAUDE.md` ; les autres agents lisent `AGENTS.md`. La gate C12 accepte l'un OU l'autre.

> Placement : `CLAUDE.md` (ou `AGENTS.md`) **à la racine du repo** (Claude Code ne charge que la racine + sous-dossiers proches). Les 4 fichiers du plan : racine aussi, ou un `/plan` — dans ce cas, ajuster les chemins listés dans `CLAUDE.md`.

### Template `CLAUDE.md` du repo cible (généré en Phase 4.3bis)

```markdown
# CLAUDE.md — [nom_projet]

> Spec persistante de l'agent, lue automatiquement par Claude Code à chaque session.
> Générée par mode-plan. Les 4 fichiers du plan sont la source de vérité — ne pas les
> recopier ici, les LIRE.

## Règle de fer (immuable)
- [Contrainte 1 — Phase 1]
- [Contrainte 2]
- [Contrainte 3]

## Plan — à lire avant toute session
- `spec_produit.md` — vision, persona, golden set §10bis[, boucle d'auto-amélioration §11 si skill]
- `archi.md` — composants, couche harnais §4bis
- `data_model.md` — entités, contrats
- `sessions_claude_code.md` — ordre des sessions + statut [DONE]
- `journal.md` — état actuel glissant + log daté (prévu/réalisé/divergence) ; se rejoue, ne se résume pas

## Discipline harnais (non négociable)
- **100% Opus** : tous les agents/sous-agents de ce projet tournent sur le modèle de session (Opus). AUCUN downgrade Haiku/Sonnet — sous forfait Max (tarif à plat) c'est sans intérêt et ça dégrade la justesse. Ne jamais coder de `model:` non-Opus.
- Sessions 1-2 : construire le harnais d'éval (golden set + assertions) AVANT les features.
- Fin de CHAQUE session : re-run l'éval ; une feature n'est « done » que si elle passe de bout en bout.
- git : workspace clean avant tout changement ; commit par session/sprint ; revert si régression.
- Fin de session : mettre à jour `sessions_claude_code.md` ([DONE] + Décisions + Divergences).

## Reset contexte
Dans le doute : nouvelle fenêtre. (cf. `sessions_claude_code.md`, champ Reset contexte par session.)
```

---

## Anatomie d'une session CC self-contained

Chaque session doit avoir :

```
[0. RESET CONTEXTE — champ obligatoire en v3.1+]
   - "nouvelle fenêtre" : ferme et rouvre CC. Défaut pour 1ère session,
     ou après session > 1h / > 100 tool calls / git reset majeur
   - "/clear" : tape /clear dans la même fenêtre. Défaut entre 2 sessions courtes
   - "continuer" : rare, uniquement pour sous-tâche très liée à la session précédente

[1. BLOC RÈGLE DE FER]
   - Contraintes immuables du projet (3-7 lignes)
   - Toujours identique entre sessions, ne jamais varier

[2. CONTEXTE DE LA SESSION]
   - Quels fichiers de plan lire en amont (paths exacts)
   - Sur quoi se concentrer dans la session

[3. TÂCHE PRÉCISE]
   - Liste numérotée d'actions concrètes
   - Mention des fichiers à créer / modifier
   - Mention des outils à utiliser si non-évidents

[4. CONTRAINTE DE PROCESS]
   - "Plan d'abord, je valide avant que tu agisses."
   - Ou variante : "Procède par petits commits."

[5. (optionnel) NOTES SPÉCIALES]
   - Pièges connus
   - Décisions déjà prises à respecter
   - Tokens / credentials disponibles
```

---

## Règle "Reset contexte" (introduite en v3.1)

| Cas | Choix | Pourquoi |
|-----|-------|----------|
| Session 1 du projet | `nouvelle fenêtre` | Démarrage propre, pas de pollution d'une autre conv |
| Session N après session N-1 courte (< 1h, < 50 tool calls, pas de drama) | `/clear` | Vide la conv, garde git/fichiers |
| Session N après session N-1 longue (> 1h, > 100 tool calls) | `nouvelle fenêtre` | Le `/clear` ne suffit pas à vider tous les caches internes |
| Session N après un gros `git reset` ou rework majeur | `nouvelle fenêtre` | CC peut garder des références mentales aux fichiers supprimés/réécrits |
| Sous-tâche immédiate (ex : Session 3 = tests de ce que Session 2 a codé) | `continuer` | Garder le contexte chaud aide, à utiliser avec parcimonie |
| CC commence à répéter / se contredire / boucler | `nouvelle fenêtre` IMMÉDIATEMENT | Contexte pollué, on ne récupère pas en `/clear` |

**Règle de fer du reset** : dans le doute, `nouvelle fenêtre`. C'est gratuit, ça reset les caches, et les fichiers de plan suffisent à remettre CC dans le bain.

---

## Template exact

```
IMPORTANT — règle de fer du projet :
- [Règle 1]
- [Règle 2]
- [Règle 3]

[Contexte session :]
On est sur le projet [nom]. Le plan est dans [dossier] :
- spec_produit.md
- archi.md
- data_model.md

Pour cette session, lis attentivement [fichier(s) spécifique(s) à cette session].

[Tâche :]
1. [Action 1, fichier(s) impacté(s)]
2. [Action 2]
3. [Action 3]

[Process :]
Plan d'abord, je valide avant que tu agisses.

[Notes — si applicable :]
- [Décision déjà prise à respecter]
- [Tokens dispo dans .env]
- [Piège connu sur ce composant]
```

---

## Bonnes pratiques

### Le prompt doit pouvoir être collé sans contexte conversationnel

Si la session précédente a duré 2h et que l'utilisateur ne se souvient pas exactement de ce qui a été décidé, le prompt doit pouvoir s'exécuter quand même grâce aux références explicites aux fichiers de plan.

### Mentionner les paths exacts, pas "le fichier de plan"

Mauvais : "Lis le plan."
Bon : "Lis `spec_produit.md` sections 4 et 6, ainsi que `archi.md` section 2.3."

### Lister les outputs attendus de la session

À la fin du prompt, expliciter ce que CC doit avoir produit :
> Tu dois avoir créé : `tools/strava_client.py`, modifié : `tests/test_strava_pull.py`. Commit : `feat: strava client (read)`.

Sinon le dev humain ne sait pas où regarder pour vérifier.

### Mention systématique du "Plan d'abord"

C'est le pattern critique de la méthode Cherny. CC propose un plan d'action, l'humain valide ou corrige, puis CC exécute. Sans ça, CC peut faire 12 fichiers d'un coup et partir dans une mauvaise direction.

### "Mise à jour du plan en fin de session"

Toujours inclure dans le prompt :
> En fin de session, mets à jour `sessions_claude_code.md` : marque cette session `[DONE]`, ajoute `Décisions prises:` + `Divergences:` si applicable.

C'est le garde-fou anti-drift entre le plan et la réalité.

---

## Anti-patterns à éviter

- **Prompt vague** : "Continue où on en était." → CC ne sait pas. Toujours répéter le contexte.
- **Prompt qui ne mentionne pas la règle de fer** → CC peut violer des contraintes architecturales clés.
- **Prompt qui ne dit pas "plan d'abord"** → CC fonce, mauvaise direction non rattrapable sans `git reset`.
- **Session qui touche > 6 fichiers** → trop gros, à splitter.
- **Session sans vérification claire** → on ne sait jamais si c'est vraiment "fini".
- **Trois sessions consécutives sans reset** → contexte pollué, baisse de qualité silencieuse. Voir tableau "Reset contexte" plus haut — la convention v3.1 f