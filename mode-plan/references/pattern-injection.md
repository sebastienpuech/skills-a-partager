# Pattern injection — chaînage mode-plan ↔ pattern-extractor

> Lu en Phase 2.2 (avant draft). Permet d'enrichir le draft initial avec
> les patterns gagnants extraits de plans passés réussis.

---

## Pourquoi ce chaînage

Le drafter de mode-plan v2.0 partait d'un template vide en Phase 2. Le critic
Phase 3 rattrapait les manques via patches append-only. Résultat : beaucoup
de patches répétitifs d'un projet à l'autre (ex : "tu n'as pas spécifié la
gestion d'erreur réseau", "il manque la section persona").

v3.0 corrige : on injecte au drafter, **avant** qu'il drafte, les patterns
récurrents extraits via `pattern-extractor` de 2-3 plans réussis (Coach,
autres projets validés). Le drafter livre donc une v0 déjà beaucoup plus
mature, et le critic se concentre sur le spécifique du projet, pas le
générique.

---

## Préparation (une fois, manuelle)

### Étape A — Identifier les plans réussis

Un plan est "réussi" si l'utilisateur a marqué le projet comme livré et que
le plan a tenu pendant l'implémentation (peu de divergences, sessions
exécutées dans l'ordre). Le user marque les plans réussis dans :

```
outputs/_mode-plan-meta/successful-plans.txt
```

Format : un chemin de dossier par ligne, ex :
```
outputs/coach/
outputs/<un-skill-pro>/
outputs/skill-auto-improver/
```

### Étape B — Extraire les patterns via pattern-extractor

Quand au moins 2 plans réussis sont listés, lancer pattern-extractor sur les
paires (template app vide) → (plan réussi). Le template fait office de
"input neutre", le plan réussi est l'"output enrichi". Pattern-extractor
voit alors le delta de chaque plan vs le template.

Commande :

```bash
# (à exécuter manuellement, hors mode-plan)
# 1. Préparer pairs.json :
#    [{"input": ".claude/skills/mode-plan/references/templates/app/spec_produit.md",
#      "output": "outputs/coach/spec_produit.md"}, ...]
# 2. Invoquer pattern-extractor sur ces paires
# 3. Sauver l'output dans outputs/_mode-plan-meta/patterns-from-real-plans.md
```

### Étape C — Format attendu du fichier patterns

mode-plan v3.0 attend `outputs/_mode-plan-meta/patterns-from-real-plans.md`
avec la structure produite par pattern-extractor (HTML markers) :

```
<!-- METADATA_START -->
# Mode-plan patterns (from N successful plans)
- Source: N plans extracted YYYY-MM-DD
<!-- METADATA_END -->

<!-- CORE_PATTERNS_START -->
## Core patterns
[patterns présents dans 80%+ des plans réussis]
<!-- CORE_PATTERNS_END -->

<!-- COMMON_PATTERNS_START -->
## Common patterns
[patterns présents dans 50-80%]
<!-- COMMON_PATTERNS_END -->

<!-- DECISION_RULES_START -->
## Decision rules
[règles IF/THEN extraites]
<!-- DECISION_RULES_END -->
```

---

## Comportement de mode-plan v3.0 en Phase 2.2

```python
# Pseudo-code
patterns_file = Path("outputs/_mode-plan-meta/patterns-from-real-plans.md")
if patterns_file.exists():
    # Charger les CORE_PATTERNS et DECISION_RULES uniquement (pas COMMON)
    inject = extract_sections(patterns_file, ["CORE_PATTERNS", "DECISION_RULES"])
    drafter_context += f"\n\n## Patterns from successful plans\n{inject}"
    log("v3.0 pattern injection : {n} patterns + {m} rules injected")
else:
    log("v3.0 pattern injection : skipped (no patterns file yet)")
```

Si le fichier n'existe pas → comportement identique à v2.0 (draft from
template only). Pas de blocage, dégradation gracieuse.

---

## Garde-fous

### G1 — Ne pas charger les patterns d'un seul plan

Le fichier doit être généré à partir de **≥ 2 plans réussis**. Avec 1 seul
plan, on ne distingue pas "pattern récurrent" de "spécificité de ce projet".
Si le fichier déclare "Source: 1 plan", mode-plan refuse l'injection et
prévient l'utilisateur :
> "Le fichier patterns-from-real-plans.md ne couvre qu'1 plan. On a besoin
> de ≥2 pour distinguer patterns vs spécificités. Ignoré pour ce draft."

### G2 — Patterns datés > 6 mois = warning

Les pratiques évoluent. Si le METADATA indique une date > 6 mois :
> "⚠ Patterns extraits il y a >6 mois. Les conventions ont peut-être bougé.
> Pertinent de relancer pattern-extractor sur les plans récents avant
> d'utiliser cette injection."

L'utilisateur peut continuer ou rafraîchir.

### G3 — Cap sur la taille injectée

L'injection ne doit pas dépasser ~2000 tokens (≈250 lignes). Au-delà, le
drafter sature et les patterns deviennent du bruit. Si patterns-from-real-plans.md
dépasse 250 lignes, n'injecter que CORE_PATTERNS (skip DECISION_RULES) ;
si toujours trop, ne prendre que les 10 premiers patterns CORE.

---

## Articulation avec la mémoire skill

Ne pas confondre :
- `outputs/_mode-plan-meta/patterns-from-real-plans.md` : patterns extraits
  des PLANS PRODUITS PAR mode-plan, utilisés pour améliorer les futurs drafts
- `outputs/<projet>/memory/issues.md` : problèmes vécus par un SKILL CRÉÉ
  PAR mode-plan, utilisés par skill-auto-improver

Les deux sont des feedback loops, mais à des niveaux différents :
- patterns-from-real-plans = meta-apprentissage de mode-plan sur lui-même
- memory/issues = apprentissage d'un skill produit par mode-plan sur lui-même

---

## Rafraîchissement recommandé

- Après chaque nouveau plan validé → ajouter à `successful-plans.txt`
- Tous les 3 nouveaux plans validés → relancer pattern-extractor pour
  rafraîchir `patterns-from-real-plans.md`
- Tous les 6 mois → revue manuelle (certaines pratiques peuvent être
  périmées même si fréquentes)
