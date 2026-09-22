# Deux skills Claude Code — `mode-plan` et `skill-creator-v12`

*(English version: [README.md](README.md))*

Deux skills que j'ai construits et que j'utilise tous les jours, partagés ici avec leur historique
daté (juillet à septembre 2026). Je ne suis pas développeur : le code est écrit par Claude Code,
je conçois, je valide et je mesure. Ce dépôt est privé et partagé sur invitation.

## Ce qu'il y a dedans

| Dossier | Ce que fait le skill | Par où commencer |
|---|---|---|
| `mode-plan/` | Avant tout projet complexe, force un plan en 4 fichiers (spécification produit, architecture, modèle de données, sessions de travail), le fait attaquer par 4 critiques en parallèle, puis un défenseur et un juge, et génère des consignes de travail autoportantes | `mode-plan/SKILL.md`, puis `mode-plan/docs/plan-v4/journal.md` |
| `skill-creator-v12/` | Crée, améliore et teste d'autres skills : cadrage, garde-fous, relecture adversariale, évaluations comparées à une version de référence | `skill-creator-v12/SKILL.md` |

## Ce que `mode-plan` a de particulier

Quatre mécanismes, chacun né d'un plan qui a échoué. Aucun n'apparaît dans les skills de
planification de `superpowers` (`brainstorming`, `writing-plans`, version 6.2.0, vérifié le
22/09/2026).

| Mécanisme | Ce qu'il fait | Pourquoi il existe | Où |
|---|---|---|---|
| **Ancrage du brief** | Avant tout débat, chaque affirmation de fait du brief (« X n'est pas installé », « le fichier n'existe pas ») est vérifiée par une commande, jamais de mémoire | Un run complet (4 critiques × 3 tours, 45 critiques confirmées, 433 k tokens, 57 minutes) a planifié un travail déjà déployé, parce que personne n'avait vérifié les prémisses du brief | `SKILL.md`, étape 1.6 |
| **Salle de débat adversariale** | 4 critiques en parallèle, puis un défenseur, puis un juge ; la fusion et la convergence sont faites par script, pas par un modèle | Un plan se juge contre ses objections, pas contre l'assurance de son auteur | `SKILL.md`, phase 3 |
| **Citations vérifiées** | Le défenseur et le juge citent le plan ; un script vérifie que chaque passage cité existe vraiment, sans aucun modèle dans la boucle | Rien ne vérifiait que leurs citations étaient réelles | `SKILL.md`, étape 3.4bis |
| **Le plan qui finit** | Chaque plan porte une condition d'arrêt globale : une recette d'acceptation gelée sur des cas réels, relue par quelqu'un d'autre que son producteur, plus des décisions figées et une règle pour les surprises | 7 plans successifs ont atteint tous leurs jalons, et le chantier n'a jamais fini | `SKILL.md`, étape 2.4ter |

Le plan final passe aussi 16 contrôles automatiques (C1 à C16, `scripts/self_diagnosis.py`), et le
skill lit l'index des leçons passées avant d'écrire. Ce sont des différences de conception, pas une
victoire mesurée : aucune comparaison de la qualité des plans face à un autre outil n'a été faite.

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
- **Une option qui n'a pas fait ses preuves a été rejetée, et le rejet conservé.** Un ensemble de
  vérificateurs, essayé le 29/07/2026 sur 8 cas réels : 0,875 sans, 0,875 avec, soit un gain nul
  pour un seuil de 0,03. Rejeté sur décision humaine, désactivé.
- **`skill-creator-v12`** : 29 tests sur ses scripts (`skill-creator-v12/tests/test_scripts.py`).

## Ce qui ne marche pas

`mode-plan` a une boucle d'auto-amélioration hebdomadaire. Elle tourne, elle journalise, et elle
n'a jamais rien amélioré : 11 passes du 02/07 au 20/09/2026, aucune n'a validé de modification, et
son score de capacité est figé à 0,6667 depuis le 28/07. Elle fait office de veille hebdomadaire ;
comme moteur d'amélioration, elle n'a rien livré. Ce journal fait partie de mes fichiers de
travail privés et n'est pas inclus dans cette copie.

## Ce que cette copie n'est pas

- Une copie de travail, extraite de mon dépôt privé de skills : l'historique est conservé, mais
  le journal d'usage personnel et les fichiers de cache ont été retirés, et les références à mes
  dépôts professionnels ou personnels remplacées par des mentions génériques.
- Pas un outil prêt à installer chez vous : certains scripts supposent mon environnement (chemins,
  tâches planifiées). Ce qui se lit ici, c'est la méthode et la manière de la mesurer.
