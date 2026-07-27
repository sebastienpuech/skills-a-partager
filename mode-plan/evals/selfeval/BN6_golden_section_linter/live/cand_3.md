# §10bis. Harnais & signal de succès

Le skill `linter-code` produit un rapport de problèmes de style sur un fichier Python ; on le juge sur sa capacité à retrouver les vrais problèmes sans en inventer.

- **Golden set** : ~15-20 fichiers Python annotés à la main, chacun accompagné de la liste des problèmes attendus, plus 2-3 fichiers propres servant de contrôle négatif.
- **Métriques** : précision et rappel par catégorie de règle. On vise rappel ≥ 0,90 et précision ≥ 0,95 — un faux positif coûte plus cher qu'un oubli.
- **Signal de succès** : sur les fichiers propres, zéro problème signalé ; sur les fichiers annotés, chaque catégorie atteint ses seuils.
- **Garde-fou anti-régression** : le golden set tourne en CI à chaque modification ; toute baisse de précision ou de rappel bloque le merge. On compare aussi à `ruff` comme oracle externe.
- **Observabilité** : journaliser les cas où l'utilisateur corrige ou rejette un signalement, pour alimenter le golden set.
