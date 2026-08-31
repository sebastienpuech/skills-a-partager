# Sessions Claude Code — [Nom du projet]

> Plan d'exécution session par session. Chaque session = un livrable testable, idéalement < 2h de travail.
> À garder ouvert en parallèle du terminal CC. Mettre à jour à la fin de chaque session.

---

## 🔒 RÈGLE DE FER — À COLLER AU DÉBUT DE CHAQUE PROMPT CLAUDE CODE

**Copie-colle ce bloc en début de CHAQUE prompt que tu donnes à Claude Code :**

```
IMPORTANT — règle de fer du projet :
- [Contrainte immuable 1 — ex : tous les appels LLM passent par tel client]
- [Contrainte immuable 2 — ex : pas de lib payante]
- [Contrainte immuable 3 — ex : stack figée à X]
- [Convention de code 1]
- [Si tu vois du code existant qui ne respecte pas ça, signale-le et corrige-le.]
```

Cette règle vaut pour **toutes les sessions de dev**. Ne pas l'oublier.

---

## 🛡️ PROTOCOLE ANTI-RÉGRESSION — OBLIGATOIRE TOUTE SESSION

**Ce protocole est non-négociable. Il prévient les régressions invisibles qui apparaissent quand on ne peut plus bisecter ce qui a cassé.**

### Étape 0 — Avant TOUT changement de code

```bash
git status                       # workspace doit être clean
# Si pas de repo : git init + créer .gitignore + premier commit
# Si workspace dirty : git stash OU commit avant de continuer
```

Sans ça, RIEN d'autre ne tourne. Pas d'exception.

### Sessions mono-mission

Un commit en fin de session suffit (`feat: session N done`).

### Sessions multi-sprints (mega-sprint, P1+P2+P3+P4, etc.)

**Commit après CHAQUE sprint interne, pas seulement à la fin de session.**

```bash
# Après P1
git commit -am "P1: <résumé>"
# → relancer baseline tests anti-régression
# → si KO : git reset --hard HEAD~1, fix, retry
# → si OK : passer à P2

# Après P2
git commit -am "P2: <résumé>"
# → idem
```

Tag à la fin : `git tag session-{N}` (ou `v{X.Y}` pour les releases).

### Procédure rollback

- Dernier commit : `git reset --hard HEAD~1`
- N commits en arrière : `git log --oneline` puis `git reset --hard <commit-id>`
- Rollback un seul fichier : `git checkout HEAD~1 -- path/to/file`

### Pourquoi c'est important (incident réel sur un chantier pro, 2026-05)

Sur le skill pro (nom retiré) Session 4 mega-sprint, le protocole d'écriture du prompt prévoyait des commits intermédiaires (`git commit -am "P{N} done"`) mais ils n'ont pas été faits. Conséquences :
- Pas de checkpoints pour rollback par sprint
- Si un retour utilisateur révèle une régression cachée, impossible de bisecter P1 vs P2 vs P3 vs P4
- Packaging part d'un état git tout mélangé

Le fix rétroactif (un commit global v1.1) a sauvé la situation mais le risque latent reste si on saute cette étape sur de futurs projets.

---

## 🧪 HARNAIS DE VÉRIFICATION — construire le signal de succès AVANT les features

> Inspiré de l'état de l'art long-running agents (Anthropic, nov. 2025) : un agent qui code sur plusieurs fenêtres échoue sans signal de réussite ni état propre. Cf. `references/harnais.md`.

**Règle non-négociable** : une des **2 premières sessions** construit le **harnais d'éval** (runner du golden set + assertions binaires de `spec_produit.md` §10bis) AVANT le gros du dev. On ne code pas de features sans moyen de savoir si elles marchent.

- **Session « Harnais »** (Session 1 ou 2) : implémente le runner des scénarios golden + les assertions ; pose `init.sh` (lancer l'app/les tests en 1 commande) + le fichier de progrès (journal append-only) + le repo git.
- **Fin de CHAQUE session** : relancer le harnais d'éval. Une feature n'est « done » que si elle passe **de bout en bout** (pas juste un unit test) — tester comme un utilisateur réel (automation navigateur si app web).
- **Incrémental** : une feature à la fois, jamais one-shot. Laisser l'environnement **propre** (commit + note de progrès) pour que la session suivante reparte d'un état mergeable.

---

## 🧭 GATES & RÉGIME DES SURPRISES (v4.4)

**Les seuls moments où l'utilisateur intervient :**
- **G1 — avant la Session 1** : valider EN BLOC la table des décisions figées
  (`spec_produit.md` §9) et la recette d'acceptation (§10ter). Un seul « oui ».
- **G2 — fin de la dernière session** : constater la recette verte → plan CLOS.

Entre G1 et G2 : **zéro question en vol.** Une session qui rencontre une question
prévue applique la décision figée et cite son numéro.

**Régime des surprises** (toute découverte hors objectif, pendant l'exécution) :
- → **une ligne dans `TROUVAILLES.md`** (constat, fichier:ligne, gravité estimée),
  et la session CONTINUE. Jamais une réouverture du plan, jamais un plan concurrent.
- Décision imprévue non couverte par la table → le choix le plus PETIT qui préserve
  l'objectif final, loggé « défaut appliqué : X » dans le journal.
- Après clôture (recette verte) : toute erreur remontée = ticket, le plan ne se
  rouvre pas.

---

## 1. Comment marche Claude Code (rappel rapide)

Claude Code est un terminal interactif. Tu lances `claude` dans le dossier projet, tu colles le prompt d'ouverture, tu suis le dialogue, tu testes, tu commits, tu fermes la session.

### 🔄 Quand vider le contexte (`/clear` ou nouvelle fenêtre)

Chaque session ci-dessous a un champ **Reset contexte** qui dit quoi faire AVANT de coller le prompt :

- **`/clear` requis** (défaut entre 2 sessions courtes) : tape `/clear` dans la même fenêtre CC, le contexte conversationnel est vidé mais l'historique git/fichiers reste.
- **Nouvelle fenêtre obligatoire** : ferme la fenêtre CC, ouvre-en une neuve avec `claude` à nouveau. Utilisé quand : la session précédente a duré > 1h, > 100 tool calls, a fait un `git reset` majeur, ou si CC commence à répéter / contredire ses propres conclusions (signal contexte pollué).
- **Continuer même fenêtre** : rare. Uniquement si on enchaîne sur une sous-tâche très proche de ce que CC vient de faire (ex : Session 3 qui ne fait que tester ce que Session 2 a codé).

Règle empirique : **dans le doute, nouvelle fenêtre.** Un contexte pollué dégrade silencieusement la qualité — c'est plus dur à diagnostiquer qu'une perte de mémoire courte rattrapée par les fichiers de plan.

**Workflow standard de session** :
1. **Reset contexte** selon le champ de la session (`/clear`, `nouvelle fenêtre`, ou `continuer`)
2. `cd <dossier projet>` puis `claude` (si nouvelle fenêtre)
3. **`git status` — clean ?** Si pas de repo : `git init` + commit initial. (cf. Protocole anti-régression ci-dessus)
4. Coller le prompt d'ouverture (avec règle de fer en tête)
5. Lire le plan que CC pr
