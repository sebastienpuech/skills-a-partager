# Exemple — Projet Coach sportif (Sébastien)

Ce projet est la référence canonique de ce que `mode-plan` produit. Il a été créé manuellement par Sébastien en mode dialogue itératif (avant l'existence de `mode-plan`), et son format a directement inspiré le skill.

## Structure du plan original

Les 4 fichiers du projet Coach :

| Fichier | Lignes | Rôle |
|---------|--------|------|
| `spec_produit.md` | ~620 | Vision, persona coach, 17 scénarios golden set, 4 patches stratégiques (v1.1, v1.2, v1.3, v1.4) |
| `archi.md` | ~1200 | Architecture multi-agent (Coach Lead + 7 spécialistes), data flows, patches archi v1.1 à v1.4 |
| `data_model.md` | ~1200 | Entités (Athlete, Séances, Convictions, KB...), patches data v1.1 à v1.4 |
| `sessions_claude_code.md` | ~600 | 8+ sessions CC numérotées + KB-1/2/3 en parallèle |

## Patterns intéressants à observer

### 1. Patches stratégiques versionnés en append-only
Au lieu de réécrire, chaque évolution majeure ajoute une section "Patches stratégiques v1.X" en fin de fichier. Préserve l'historique de pensée, lisible par le LLM en runtime.

Exemple `spec_produit.md` :
- Corps initial = scénarios 1-13 + persona
- Patch v1.1 = ajout persona "fortes convictions, pas serviteur"
- Patch v1.2 = ajout des "leviers anti-déterminisme" (L1-L4)
- Patches incrémentaux préservent ce qui marche

### 2. Règle de fer en début de chaque prompt CC
`sessions_claude_code.md` ouvre par un bloc :
> IMPORTANT — règle de fer du projet (cf. docs/archi.md patch v1.4-arch-12) :
> - Tous les appels LLM passent par agents/llm_client.py
> - Aucun import direct de la lib `anthropic`
> - [...]

Et chaque session répète cette règle dans son prompt. Anti-drift architectural inter-sessions.

### 3. Scénarios = golden set + jeu de test
Patch v1.2 de `spec_produit.md` clarifie :
> "Ces scénarios ne sont PAS exhaustifs. Ils servent de jeu de tests pour valider que le coach se comporte correctement sur des cas représentatifs. Ils ne sont jamais chargés dans le contexte du coach — il ne sait même pas qu'ils existent."

Double fonction spec/test, sans que le contenu pollue le runtime de l'agent.

### 4. Sessions parallèles documentées
Sessions principales (1-8) + sessions KB en parallèle (KB-1, KB-2, KB-3, KB-QA). Chacune indépendante après une dépendance initiale.

### 5. Vérifications + commit attendu par session
Chaque session du `sessions_claude_code.md` finit par :
- **Vérifications après la session** : checks concrets (commande à lancer, résultat attendu)
- **Commit attendu** : message de commit suggéré, convention conventional commits

### 6. Sessions complexes — re-versionnées
KB-2 et KB-3 ont chacune une version v1.0 puis une v1.3 plus mature. Le fichier garde les deux et flag que v1.0 est obsolète, sans la supprimer (préserve la trace de l'apprentissage).

## Pourquoi ce projet justifie mode-plan

Si on applique la grille de détection mode-plan au projet Coach :

- ✅ Plus de 3 sessions CC ? **Oui, 8+ sessions + KB en parallèle**
- ✅ Plusieurs composants/agents qui collaborent ? **Oui, Coach Lead + 7 spécialistes**
- ✅ Golden set de scénarios testables ? **Oui, 17 scénarios**
- ✅ Décisions d'archi à figer avant de coder ? **Oui, choix LLM client, embeddings, DB, pattern d'orchestration**

4/4 critères → mode-plan justifié à 100%.

## Limite de l'exemple

Ce projet a été produit *avant* mode-plan, donc en dialogue itératif libre. Mode-plan vise à reproduire la même qualité de plan, mais avec :
- Un format imposé (pas besoin de réinventer la structure à chaque projet)
- Une adversarial review systématique (qui aurait peut-être catché plus tôt certains trous archi)
- Un handoff CC standardisé (les prompts du projet Coach ont été affinés au fil des sessions, mode-plan les produit propres d'emblée)

## Fichiers à consulter

Les 4 fichiers complets du projet Coach sont disponibles dans les uploads de Sébastien sur Cowork (trop volumineux pour les inclure ici tels quels). Sur cette session : voir `uploads/spec_produit.md`, `uploads/archi.md`, `uploads/data_model.md`, `uploads/sessions_claude_code.md`.
