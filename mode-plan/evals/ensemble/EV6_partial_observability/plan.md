# Plan — skill webhook-router (extrait)

## 1. Vision
Route les webhooks entrants vers le bon handler selon leur type.

## 6. Signal de succès
- 7 webhooks types, handler cible attendu asséré.

## 8. Observabilité
- en cas d'erreur, on logue le message d'exception.

## 9. Garde-fous
- signature vérifiée, rate-limit 50/s.
