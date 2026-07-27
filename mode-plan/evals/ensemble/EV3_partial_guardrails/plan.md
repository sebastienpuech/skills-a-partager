# Plan — skill sync-fichiers (extrait)

## 1. Vision
Un skill qui synchronise un dossier local vers un stockage distant.

## 6. Signal de succès
- 5 scénarios de sync rejoués, état distant comparé à l'attendu (assertion binaire).

## 9. Garde-fous
- timeout 30s par fichier ; retry x3 sur erreur réseau.
- idempotence : re-synchroniser un fichier déjà à jour ne fait rien.
