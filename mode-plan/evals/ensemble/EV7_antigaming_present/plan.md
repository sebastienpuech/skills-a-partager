# Plan — skill note-grader (extrait)

## 1. Vision
Un skill qui note automatiquement des copies d'élèves selon un barème.

## 6. Signal de succès
- 15 copies de référence notées par un enseignant (note attendue).
- Le moteur de notation tourne en environnement isolé : il n'a AUCUN accès aux notes attendues du golden set pendant l'essai (essai aveugle). La vérification compare sa note à l'attendu après coup.

## 9. Garde-fous
- note bornée [0,20], refus si copie illisible.
