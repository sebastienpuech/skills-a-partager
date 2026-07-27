## §10bis. Harnais & signal de succès

**Signal de succès** : sur un jeu doré de fichiers Python annotés à la main (au moins 10 fichiers mêlant code propre et violations connues), le skill retrouve chaque violation attendue à la bonne ligne et n'en invente aucune.

- **Métriques** : précision (aucun faux positif sur le code propre) et rappel (aucune violation manquée) mesurés contre les annotations de référence. Cible : 100 % sur le jeu doré.
- **Oracle** : comparer la sortie du skill au diagnostic de `ruff check` sur les mêmes fichiers — tout écart est un bug à trancher.
- **Cas limites** : fichier vide, fichier sans violation, syntaxe invalide (doit signaler proprement, pas planter).
- **Rouge/vert** : un fichier conforme passe au vert ; un fichier avec une violation injectée repasse au rouge.
- **Régression** : rejouer le jeu doré après chaque modification ; aucun écart toléré avant de livrer.
