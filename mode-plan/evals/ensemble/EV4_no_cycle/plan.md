# Plan — skill pipeline-image (extrait)

## 3. Composants
- loader.py, resizer.py, encoder.py

## 4. Flux
- loader → resizer → encoder (pipeline unidirectionnel). Chaque étape reçoit son entrée de la précédente et retourne sa sortie ; aucune étape ne rappelle une étape amont. L'état passe par valeur, pas de singleton partagé.

## 6. Signal de succès
- 6 images de référence, sortie encodée comparée à l'attendu (hash).
