# Workflow — détail des 4 phases de mode-plan

> Lire ce fichier en cas de confusion sur une étape du SKILL.md, ou pour gérer un edge case.

---

## Phase 1 — Élicitation (détail)

### Pourquoi 1 tour AskUserQuestion + chat libre

`AskUserQuestion` est limité à 4 questions par tour et propose des choix discrets. Excellent pour : type, mode, oui/non. Mauvais pour : texte long, listes ouvertes.

Donc : 1 tour AskUserQuestion (3 questions de classification) + 1 prompt chat libre pour le contenu riche (vision, règles de fer, scope, nom).

### Si l'utilisateur ne répond pas tout

Redemander **une fois**, en listant explicitement ce qui manque :
> "Il me manque encore : [liste]. Sans ça je ne peux pas drafter un plan utile. Tu peux compléter ?"

Si toujours incomplet → présenter un plan avec champs en `[À COMPLÉTER]` et marquer le doc comme "Status: incomplet, à compléter manuellement avant exécution".

### Si l'utilisateur dit "skip" sur le brief libre

C'est probable qu'il pense que c'est de la friction inutile. Lui expliquer en 1 phrase :
> "Le brief libre n'est pas optionnel — sans la vision et les règles de fer, le critic n'a rien à challenger et les prompts CC ne contiendront pas tes contraintes immuables. C'est ~3 min de saisie pour gagner des heures."

S'il insiste → produire un plan dégradé avec placeholders, marqué "incomplet".

---

## Phase 2 — Draft du plan (détail)

### Pourquoi 3 fichiers et pas 4

Le 4e fichier (`sessions_claude_code.md`) est généré APRÈS la review. Logique :
- Si le critic patche l'archi, ça impacte le découpage en sessions
- Si on génère les 4 d'un coup, le critic a 4x plus à reviewer (coût tokens)
- Le critic ne peut pas vraiment challenger des sessions sans avoir vu l'archi cristallisée

### Taille cible des fichiers

| Fichier | Taille cible | Plage acceptable |
|---------|--------------|------------------|
| spec_produit.md | 300-600 lignes | 100-1000 |
| archi.md | 200-400 lignes | 80-800 |
| data_model.md | 150-300 lignes | 50-600 |
| sessions_claude_code.md | dépend du nb de sessions | 1 session ≈ 30-60 lignes |

Si un fichier dépasse 1000 lignes → probablement à splitter (sous-fichiers `references/<topic>.md` dans le projet).

### Mode iterate_existing

Si l'utilisateur a un plan existant à challenger :
1. Demander les chemins des fichiers (peut être un dossier ou des fichiers individuels)
2. Lire les 3 fichiers (ou les 4 si sessions_claude_code.md existe déjà — alors review aussi celui-là)
3. Détecter la version actuelle : grep `## Patches stratégiques v(\d+\.\d+)` → prendre le max, incrémenter pour la nouvelle review
4. Skipper Phase 2, passer en Phase 3

---

## Phase 3 — Adversarial review (détail)

### Pourquoi 1 critic composite et pas 3 parallèles

V1 simplification (cf. décisions design dans le plan initial v1.1). Avantages :
- 1 seul JSON à parser → moins de risque de désaccord
- Coût tokens ÷ 3
- Debug du prompt critic plus facile

Si Sébastien constate après 5+ utilisations que le critic est "mou" ou rate des angles → splitter en 3 critics distincts (architect-skeptic, pragmatist, execution-simulator) et ajouter un synthétiseur séquentiel. Le pattern est documenté pour un upgrade futur.

### Gestion JSON invalide

Cas 1 — JSON parsable mais champs invalides (enum hors liste, type incorrect) :
- Patcher silencieusement les champs invalides (ex: gravité inconnue → "moyenne") et logger un warning
- Continuer le flow

Cas 2 — JSON impossible à parser :
- Relance unique avec message d'erreur explicite
- Si re-échec → présenter le brut à l'utilisateur, demander "tu veux que j'extrais les patches manuellement, ou on skip la review pour ce projet ?"

Cas 3 — Le critic refuse d'output (sécurité, off-topic, etc.) :
- Rare mais possible. Présenter à l'utilisateur, lui demander de reformuler le projet si offensant.

### Cap d'itérations sur major_revision

- 1ère itération : verdict = major_revision → repartir en Phase 2 avec les patches comme guide
- 2e itération : verdict = major_revision → demander à l'utilisateur "le critic n'est jamais satisfait. Soit le projet est mal spécifié, soit le critic est trop dur. Que veut-on faire ?"
- Pas de 3e itération automatique

---

## Phase 4 — Patch + sessions_cc.md (détail)

### Append-only pour les patches

Pourquoi : préserve l'historique de pensée. Les fichiers contiennent leur évolution dans l'ordre chronologique.

Format obligatoire en fin de chaque fichier patché :

```markdown

---

## Patches stratégiques v[X.Y]

> Issus de [source : adversarial review automatique du DATE / retour utilisateur / etc.]

### Patch [gravité haute|moyenne|basse] — [sujet court]

**Diagnostic** : [1-3 phrases factuelles : ce qui ne va pas et pourquoi.]

**Modification** : [contenu à ajouter / changer, prêt à coller. Peut inclure de nouveaux scénarios, de nouvelles contraintes, des reformulations.]

### Patch [...] — [...]
[Idem pour chaque patch.]
```

### Génération de sessions_claude_code.md

Doit contenir, dans l'ordre :
1. En-tête avec **règle de fer consolidée** (issue de Phase 1)
2. Section "Comment marche Claude Code" (copier depuis le template)
3. Section "Prérequis avant la session 1" (custom au projet)
4. Les sessions, numérotées, chacune avec : status, objectif, prérequis, prompt, vérifications, commit attendu, mise à jour du plan
5. Section "Sessions en parallèle" (si applicable)
6. Section "Au-delà du MVP"
7. Section "Si tu galères"
8. Section "Récap des fichiers"

Chaque prompt CC doit être **self-contained** : un dev qui lit uniquement ce prompt doit pouvoir exécuter la session sans aller chercher d'info ailleurs.

### Découpage en sessions

Règles :
- Une session = un livrable testable
- ~2h de travail max (au-delà, splitter)
- Une session = max 5-6 fichiers touchés
- Dépendances explicites (Session N requires Sessions M, P)
- Tout commit attendu de chaque session doit être nommé en convention conventional commits

---

## Edge cases divers

### L'utilisateur change d'avis en cours de flow

Toujours possible. Si Phase 2 ou Phase 3 et l'utilisateur dit "en fait on change tout" → reset au début de Phase 1, garder les fichiers déjà écrits comme backup (`outputs/<nom_projet>/_backup_v0/`).

### Le projet a un nom déjà utilisé

Si `outputs/<nom_projet>/` existe déjà :
- Si mode `iterate_existing` → OK, c'est attendu
- Sinon → demander : "Le dossier existe. Tu veux : (a) écraser, (b) suffixer (-v2, -v3), (c) annuler ?"

### Le critic ne trouve rien à patcher

Verdict `go` direct. C'est rare mais possible pour un plan déjà bien pensé (ex: mode `iterate_existing` sur un plan déjà mature). Pas de patch, sauter directement à la génération de sessions_claude_code.md.

### Task tool indisponible

Si le skill est invoqué hors Cowork (impossible normalement, mais par sécurité) :
- Détection : tenter d'instancier un Task et catch l'erreur
- Fallback : exécuter le critic en inline (le LLM principal fait les 3 angles dans sa propre réponse). Moins propre mais permet de finir.
- Marquer dans les fichiers : "adversarial review exécutée en mode dégradé (inline)".
