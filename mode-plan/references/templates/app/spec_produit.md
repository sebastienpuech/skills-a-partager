# Spec produit — [Nom du projet]

> Document de référence pour le développement. Construit en dialogue, itératif.
> Status : EN COURS — section [X] à compléter.

---

## 1. Vision en une phrase

[Une seule phrase qui dit à quoi sert le projet, pour qui, et pourquoi c'est mieux que l'alternative.]

## 2. Utilisateur

**[Nom / type d'utilisateur]**.

Profil détaillé : [pointe vers un fichier `references/profil-user.md` si pertinent, ou détaille ici].

Points saillants à garder en tête pour la conception :
- [trait 1 qui contraint le design]
- [trait 2]
- [trait 3]
- [contraintes de vie / contexte qui impactent l'usage]

## 3. Persona / ton / philosophie (si pertinent)

[Si le produit a un agent conversationnel, un assistant, ou une voix propre — décrire ici. Sinon supprimer cette section.]

### Identité
[Nom de l'agent / persona.]

### Voix
- [trait de communication 1]
- [trait 2]
- [trait 3]

### Philosophie / convictions
[Ce en quoi le produit "croit". Permet au LLM de raisonner depuis un socle quand un cas n'est pas couvert.]

### Limites assumées
- [ce que le produit ne fait pas]
- [ce qu'il refuse de faire]

## 4. Objectifs

### Objectif long terme
[Cible à 6-12 mois.]

### Objectif court terme (MVP)
[Cible à 1-3 mois.]

### Étalon de succès (référence)
[Comment on saura qu'on s'approche du but.]

## 5. Périmètre fonctionnel

### MVP (V1)
- [feature 1]
- [feature 2]
- [feature 3]

### V2 (après MVP fonctionnel)
- [feature 1]
- [feature 2]

### Hors scope (jamais ou très tard)
- [explicitement exclus]

## 6. Scénarios — Golden set

> **Objectif** : 5 à 15 scénarios concrets qui couvrent l'espace utile.
> Servent de spec produit ET de jeu de tests pendant le développement.
> **Important** : ces scénarios ne sont PAS exhaustifs. Le produit doit gérer naturellement
> des centaines de cas non listés, en s'appuyant sur sa philosophie + son contexte.

Format de chaque scénario :
- **Contexte** : situation, état, données dispo
- **Trigger** : qui parle en premier
- **Input** : ce que l'utilisateur dit / ce que le système détecte
- **Output idéal** : ce que le produit fait / répond
- **Données nécessaires** : ce qu'il faut savoir pour produire cet output
- **Patterns à retenir** : ce que ce scénario enseigne sur la signature du produit

### Scénario 1 — [titre court]

**Contexte** : ...

**Trigger** : ...

**Input** : ...

**Output idéal** :
> ...

**Données nécessaires** :
- ...

**Patterns** : ...

---

[Répéter pour les autres scénarios. Numérotation continue.]

---

## 6.bis Patterns transverses (extraits des scénarios)

> Ces patterns sont la "signature" du produit. Doivent être présents dans les prompts système / la logique métier et servir de critères d'évaluation.

1. **[Pattern 1]** : ...
2. **[Pattern 2]** : ...
3. **[Pattern 3]** : ...

## 7. Données nécessaires

### Sources externes
- [API 1, MCP 1, etc.]

### Inputs manuels
- [ce que l'utilisateur fournit en chat ou via formulaire]

### État dérivé / calculé
- [ce que le système calcule à partir des sources]

## 8. Architecture cible (rappel — détails dans `archi.md`)

```
[diagramme texte simple des composants principaux et de leurs flux]
```

## 9. Décisions à trancher

| Décision | Options | Status |
|----------|---------|--------|
| [décision 1] | [option A / option B] | À trancher |
| [décision 2] | [...] | À trancher |

## 10. Critères de succès

Comment on saura que le produit est bon :
- [critère 1]
- [critère 2]
- [critère 3]

## 10bis. Harnais & signal de succès (v3.3)

> Comment le produit *sait* qu'il marche. Sans ça, le reste du plan est aveugle. Cf. `references/harnais.md` (H1/H2).

**Golden set + assertions** : transformer les scénarios du §6 en jeu **tenu à l'écart**, avec des assertions **binaires** (vrai/faux) rejouées à **chaque** changement. Idéalement vérifiables sans LLM (esprit RLVR : on ne valide que ce qui passe un check programmatique).

| Sortie à vérifier | Assertion (binaire si possible) | Vérifieur |
|-------------------|---------------------------------|-----------|
| [sortie 1] | [check exact] | [script / regex / LLM-judge ancré] |

**Deux suites distinctes** (ne pas confondre) :

| Suite | Pass-rate cible | Rôle | Quand elle bouge |
|-------|-----------------|------|------------------|
| *Capability* | bas au départ (la colline à gravir) | mesure la progression vers le but | un cas saturé (toujours vert) **gradue** vers la suite regression |
| *Regression* | ~100 % en permanence | garde-fou anti-régression | rejouée à **chaque** changement ; un rouge = on a cassé quelque chose |

**Règles de grading** :
- **Grade-the-output-not-the-path** : on évalue l'**état final / la sortie**, pas la séquence d'étapes ou d'appels d'outils (trop fragile). « Done » = état observable, pas l'auto-déclaration de l'agent.
- **Partial credit** sur les sorties multi-composantes (« 4 faits attendus sur 5 »), pas tout-ou-rien.
- Tester les cas **should-fire ET should-not-fire** (un eval unilatéral crée une optimisation unilatérale).

**Vérifieur vs générateur** : la couche qui vérifie est **distincte** de celle qui génère. Un vérifieur cheap et fiable permet un générateur plus simple (couche la plus rentable du harnais). Le grader doit être **non-gamable** : essai en environnement propre, pas de fuite des réponses attendues, check qu'on ne peut pas satisfaire trivialement (optimiser contre une cible vérifiable invite au reward-hacking).

**Prudence LLM-as-judge** : utile, mais à **ancrer sur des cas réels** — les utilisateurs/juges 100% simulés par LLM sont des proxies non fiables (*Lost in Simulation*). Golden set réel > juge LLM seul.

## 11. Boucle d'auto-amélioration (si type=skill)

> Comment le skill *s'améliore tout seul* sur ses vrais échecs, après livraison. L'union du signal de succès (§10bis) et de la mémoire. Cf. `references/harnais.md`. Section vide / supprimée pour un livrable non-skill.

| Pièce | Ce que le plan définit |
|-------|------------------------|
| **Signal rejouable** | golden set + assertions binaires du §10bis (la fitness du loop) |
| **Mémoire d'exécution** | `memory/interactions.jsonl` (log) · `memory/issues.md` (échecs) · `memory/proposed_fixes.md` (audit) |
| **Moteur** | `skill-auto-improver` : lit issues + golden set → patch → **commit si score↑ / revert sinon** |
| **Déclencheur** | tâche planifiée (ex. nuit / semaine) qui lance la passe — sans ça, pas de loop |
| **Métrique + arrêt** | score cible, max itérations, condition de plateau |
| **Garde-fou anti-gaming** | le moteur optimise *contre* le golden set → assertions non-gamables, essais isolés (sinon il apprend à tricher) |

**Règle** : pas de déclencheur + mémoire = ce n'est pas une boucle, juste un test ponctuel.

---

## 12bis. Limites LLM pour ce skill (+ contournements)   [OBLIGATOIRE si type=skill/agent]

> Rempli en Phase 2 via `diagnostic-plafonds` sur le DOMAINE + les TECHNIQUES du skill.
> On ne peut pas dépasser un plafond qu'on n'a pas nommé. (harnais H9, gate C14)

| # | Limite du LLM pour CETTE tâche | Classe | Preuve / symptôme observé | Contournement | Cas golden |
|---|--------------------------------|--------|---------------------------|---------------|------------|
| LM1 | [ce que le modèle ne fait PAS de façon fiable ici] | contournable-ingénierie \| structurel-IA-seule \| irréductible | [où/quand ça casse, exemple concret] | [outil \| vérifieur \| décomposition \| human-in-loop \| → labo-recherche] | [id du cas §10bis] |

**Règles de remplissage :**
- **contournable-ingénierie** → un outil/scaffold la neutralise (ex. calcul délégué à du code, RAG pour un fait, schéma imposé). Prouver par un cas golden should-fire (avec contournement) + should-fail (sans).
- **structurel-IA-seule** → décomposition + vérifieur explicite, OU escalade à `labo-recherche` (invention de contournement). Ne pas prétendre l'avoir résolu si le golden ne le prouve pas.
- **irréductible** → borner le scope du skill pour l'éviter, et l'inscrire dans « Limites connues » — jamais la cacher.
- Toute limite « contournable/structurelle » SANS cas golden associé = trou (le `critic-harnais` H9 la flague).

---

*Document maintenu par : dialogue itératif. Dernière màj : [date].*
