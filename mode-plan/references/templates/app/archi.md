# Architecture — [Nom du projet]

> Décisions techniques structurantes. À lire en parallèle de `spec_produit.md` et `data_model.md`.

---

## 1. Vue d'ensemble (1 schéma)

```
[Diagramme ASCII ou Mermaid des composants principaux.
 Doit tenir en 30 lignes. Si plus complexe, splitter en plusieurs diagrammes par sous-section.]
```

## 2. Composants

### 2.1 [Composant principal 1]
**Rôle** : ...
**Stack** : [langage, framework]
**Inputs** : ...
**Outputs** : ...
**Dépendances** : [autres composants, services externes]

### 2.2 [Composant principal 2]
[Idem.]

### 2.3 [...]

## 3. Flux principaux

### 3.1 [Flux 1 — ex: événement A déclenche action B]
```
[étape 1] → [étape 2] → [étape 3]
```
**Synchrone / asynchrone** : ...
**Gestion d'erreur** : ...

### 3.2 [Flux 2]
[Idem.]

## 4. Patterns d'orchestration (si multi-agent ou orchestrateur)

**Pattern choisi** : [Debate Room / Panel d'Experts / Refinement Loop / Red Team / Tournament / autre]

**Justification** : pourquoi ce pattern plutôt qu'un autre, vu le type de tâche.

**Agents impliqués** :
- [Agent 1] : rôle, prompt résumé
- [Agent 2] : ...

**Contrats inter-agents** : format JSON ou schéma des messages échangés.

**Garde-fous** :
- Circuit-breaker : [conditions]
- Auto-diagnostic : [comment l'orchestrateur sait qu'il dérive]
- Cap d'itérations : [valeur, raison]

## 4bis. Couche Harnais (v3.3 — context · vérification · mémoire · observabilité · garde-fous)

> L'environnement et la boucle de feedback autour du modèle. Cf. `references/harnais.md` (H1–H8). Le modèle fournit la pensée ; cette couche fournit ce qu'il **voit**, **peut faire**, et **peut vérifier**.

- **Context engineering** : budget de contexte par étape ; récupération *just-in-time* (identifiants légers chargés à l'exécution) vs pré-chargement ; long-horizon → compaction → note-taking → sous-agents.
- **Vérification** : où vit le vérifieur, quoi il check (renvoie au golden set de `spec_produit.md` §10bis).
- **Mémoire & état** : comment l'état survit entre sessions/fenêtres (progress file, journal append-only, checkpoints git, reprise après erreur).
- **Observabilité** : traces/artefacts conservés pour savoir *pourquoi* un run échoue, pas seulement qu'il échoue.
- **Garde-fous** : budgets (tokens/steps/temps), timeouts, caps d'itérations ; human-in-the-loop + sandbox sur actions sensibles ; anti-injection si ingestion de contenu non fiable.
- **Outils** : set minimal, non-redondant, erreurs actionnables (le modèle se corrige seul).
- **Justification du fan-out** : pour chaque multi-agent, le test empirique — si on le remplace par 1 appel d'un bon modèle, le score golden baisse-t-il ? Sinon, simplifier (la redondance cognitive est une taxe ; la vraie parallélisation sur contenu distinct reste valable).

## 5. Décisions techniques figées

| Décision | Choix | Pourquoi | Alternative écartée |
|----------|-------|----------|---------------------|
| Langage backend | ... | ... | ... |
| DB | ... | ... | ... |
| Hosting | ... | ... | ... |
| Format de comm interne | ... | ... | ... |

## 6. Structure du repo

```
projet/
├── [dossier 1]/
│   └── [sous-dossier]/
├── [dossier 2]/
├── docs/
├── tests/
└── infra/
```

## 7. Sécurité, secrets, env

- Secrets : [comment ils sont gérés, où ils vivent]
- Variables d'env : [liste]
- Auth : [si applicable]

## 8. Observabilité

- Logs : [niveau, format, destination]
- Erreurs : [stratégie de remontée]
- Monitoring : [optionnel pour MVP]

## 9. Limitations connues (acceptées)

- [trade-off 1 et pourquoi on l'accepte pour le MVP]
- [trade-off 2]

## 10. Évolutions prévues (V2+)

- [feature qui changerait l'archi et comment]

---

*Dernière màj : [date].*
