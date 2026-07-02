## §10bis. Harnais & signal de succès

Le skill marche si un rappel programmé arrive à l'heure prévue, avec le bon texte, une seule fois. Vérification concrète :

- **Test bout-en-bout** : programmer un rappel à T+2 min, confirmer réception entre T+2:00 et T+2:30, texte exact, un seul message.
- **Persistance / survie redémarrage** : rappel à T+10 min, tuer puis relancer le bot ; le rappel part quand même (état en base, pas en RAM).
- **Idempotence** : après envoi, le rappel est marqué `done` en base — aucun doublon même si le scheduler repasse.
- **Cas limites** : heure déjà passée → refus explicite ; veille/reveil Windows → le rappel en retard part au réveil.
- **Observabilité** : chaque envoi loggé (id, heure prévue, heure réelle, statut).
- **Golden set** : 3-4 rappels types rejoués après chaque modif du scheduler.
