## §10bis. Harnais & signal de succès

Le skill marche si, sur un **golden set de ~15 paires EN→FR** (phrases courtes, registres variés), les traductions passent ces contrôles :

- **Fidélité** : sens préservé, rien ajouté/omis — vérifié par back-translation FR→EN qui doit rester équivalente à l'original.
- **Français natif** : orthographe/accords/typographie corrects (accents, apostrophes, espaces insécables), zéro calque anglais.
- **Sortie propre** : uniquement la traduction, sans préambule ni note.
- **Robustesse entrée** : input déjà en français → renvoyé tel quel ; input vide → message d'erreur clair.

**Signal rouge** (régression) : baisse du taux de réussite sous 14/15, ou apparition de préambules. Rejouer le golden set après chaque édition du prompt.
