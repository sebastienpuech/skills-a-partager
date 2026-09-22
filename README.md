# Deux skills Claude Code — `mode-plan` et `skill-creator-v12`

Deux skills que j'ai construits et que j'utilise tous les jours, partagés ici avec leur historique
daté (juillet à septembre 2026). Je ne suis pas développeur : le code est écrit par Claude Code,
je conçois, je valide et je mesure. Ce dépôt est privé et partagé sur invitation.

## Ce qu'il y a dedans

| Dossier | Ce que fait le skill | Par où commencer |
|---|---|---|
| `mode-plan/` | Avant tout projet complexe, force un plan en 4 fichiers (spécification produit, architecture, modèle de données, sessions de travail), le fait attaquer par 4 critiques en parallèle, puis un défenseur et un juge, et génère des consignes de travail autoportantes | `mode-plan/SKILL.md`, puis `mode-plan/docs/plan-v4/journal.md` |
| `skill-creator-v12/` | Crée, améliore et teste d'autres skills : cadrage, garde-fous, relecture adversariale, évaluations comparées à une version de référence | `skill-creator-v12/SKILL.md` |

## Ce qui est mesuré, et où le vérifier

Chaque chiffre renvoie au fichier qui le contient.

- **`mode-plan` se vérifie par des scripts, pas par l'impression qu'il laisse.** Relevé du
  journal (`mode-plan/docs/plan-v4/journal.md`) : `run_evals` 19 sur 19, rejeu du débat
  adversarial 6 sur 6.
- **Une option n'est branchée que si son gain dépasse un seuil fixé d'avance.** La génération de
  plusieurs candidats (« best-of-N ») : score moyen 0,45 sans, 0,5625 avec, sur 8 cas choisis
  avant la mesure ; seuil de gain 0,03. Elle reste optionnelle. Même journal.
- **Le skill a été audité contre lui-même, et l'audit l'a pris en défaut.** Rapport du 03/07/2026
  (`mode-plan/docs/audit-2026-07-03-skill-reviewer-v2/rapport.md`) : le cadrage tient, mais un
  vérificateur passait au vert si l'on supprimait simplement le dossier de cas réservés. Pour un
  skill dont la thèse est « la confiance vient des vérificateurs », c'est le défaut qui compte le
  plus : il est écrit, pas caché.
- **Les cas d'évaluation sont publiés avec leurs verdicts**, y compris les plans rejetés
  (`mode-plan/evals/ensemble/`).
- **`skill-creator-v12`** : 29 tests sur ses scripts (`skill-creator-v12/tests/test_scripts.py`).

## Ce que cette copie n'est pas

- Une copie de travail, extraite de mon dépôt privé de skills : l'historique est conservé, mais
  le journal d'usage personnel et les fichiers de cache ont été retirés, et les références à mes
  dépôts professionnels ou personnels remplacées par des mentions génériques.
- Pas un outil prêt à installer chez vous : certains scripts supposent mon environnement (chemins,
  tâches planifiées). Ce qui se lit ici, c'est la méthode et la manière de la mesurer.
